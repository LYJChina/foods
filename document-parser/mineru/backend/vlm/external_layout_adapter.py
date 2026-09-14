"""Adapt OpenAI-compatible JSON layout output to MinerU VLM blocks."""

from __future__ import annotations

import json
import re
from copy import copy
from dataclasses import is_dataclass, replace
from collections.abc import Sequence
from typing import Any

from loguru import logger
import pypdfium2 as pdfium

from mineru_vl_utils.mineru_client import ContentBlock
from mineru.utils.pdf_text_tool import get_page
from mineru.utils.pdfium_guard import close_pdfium_document, open_pdfium_document
from mineru.utils.multimodal_config import MULTIMODAL_LAYOUT_MAX_TOKENS, MULTIMODAL_LAYOUT_PROMPT


_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def _json_candidates(output: str) -> list[str]:
    text = output.strip()
    candidates = [text]
    match = _FENCED_JSON_RE.search(text)
    if match:
        candidates.insert(0, match.group(1).strip())

    for opener, closer in (("[", "]"), ("{", "}")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start >= 0 and end > start:
            candidates.append(text[start : end + 1])
    return candidates


def _load_layout_payload(output: str) -> Any:
    for candidate in _json_candidates(output):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("layout response does not contain valid JSON")


def _layout_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("layout", "blocks", "items", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _normalize_bbox(value: Any) -> list[float] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 4:
        return None
    try:
        coords = [float(item) for item in value]
    except (TypeError, ValueError):
        return None

    # The model uses MinerU's 0-1000 coordinate space.
    if max(coords) > 1:
        coords = [coord / 1000.0 for coord in coords]
    x1, y1, x2, y2 = coords
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
        return None
    return [x1, y1, x2, y2]


def _normalize_confidence(value: Any) -> float | None:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return None
    return confidence if 0 <= confidence <= 1 else None


def _normalize_char_boxes(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for char_item in value:
        if isinstance(char_item, dict):
            char = char_item.get("char", char_item.get("text"))
            raw_bbox = char_item.get("bbox_2d", char_item.get("bbox"))
            raw_confidence = char_item.get(
                "confidence",
                char_item.get("ocr_confidence", char_item.get("score")),
            )
        elif isinstance(char_item, Sequence) and not isinstance(char_item, (str, bytes)) and len(char_item) == 6:
            char, *raw_coords, raw_confidence = char_item
            raw_bbox = raw_coords
        else:
            continue
        bbox = _normalize_bbox(raw_bbox)
        if not isinstance(char, str) or len(char) != 1 or bbox is None:
            continue
        item: dict[str, Any] = {"char": char, "bbox": bbox}
        confidence = _normalize_confidence(raw_confidence)
        if confidence is not None:
            item["confidence"] = confidence
        normalized.append(item)
    return normalized


def parse_bbox_json_layout(output: str) -> list[ContentBlock]:
    """Convert model ``bbox_2d``/``text_content`` JSON to MinerU text blocks."""
    payload = _load_layout_payload(output)
    blocks: list[ContentBlock] = []
    for item in _layout_items(payload):
        bbox = _normalize_bbox(item.get("bbox_2d", item.get("bbox")))
        content = item.get("text_content", item.get("content"))
        if bbox is None or not isinstance(content, str) or not content.strip():
            continue
        block = ContentBlock("text", bbox, content=content.strip())
        confidence = _normalize_confidence(
            item.get("confidence", item.get("ocr_confidence", item.get("score")))
        )
        if confidence is not None:
            block["ocr_score"] = confidence
        char_boxes = _normalize_char_boxes(
            item.get("char_boxes", item.get("char_bboxes", item.get("characters")))
        )
        if char_boxes:
            block["char_boxes"] = char_boxes
        blocks.append(block)
    return blocks


def _bbox_coords(value: Any) -> tuple[float, float, float, float] | None:
    try:
        coords = tuple(float(item) for item in value)
    except (TypeError, ValueError):
        return None
    return coords if len(coords) == 4 else None


def native_text_layout(page: Any, min_chars: int) -> list[ContentBlock] | None:
    """Build text blocks from an embedded PDF text layer when it is substantial."""
    page_data = get_page(page)
    page_width = float(page_data["width"])
    page_height = float(page_data["height"])
    if page_width <= 0 or page_height <= 0:
        return None

    blocks: list[ContentBlock] = []
    native_chars = 0
    for raw_block in page_data.get("blocks", []):
        texts: list[str] = []
        block_bbox: list[float] | None = None
        for line in raw_block.get("lines", []):
            line_text = "".join(
                str(span.get("text", ""))
                for span in line.get("spans", [])
                if isinstance(span, dict)
            ).replace("\r", "").replace("\n", "").strip()
            line_coords = _bbox_coords(line.get("bbox"))
            if line_text:
                texts.append(line_text)
                native_chars += len(line_text)
            if line_coords:
                x1, y1, x2, y2 = line_coords
                current = [x1, y1, x2, y2]
                if block_bbox is None:
                    block_bbox = current
                else:
                    block_bbox = [
                        min(block_bbox[0], current[0]),
                        min(block_bbox[1], current[1]),
                        max(block_bbox[2], current[2]),
                        max(block_bbox[3], current[3]),
                    ]
        if not texts or block_bbox is None:
            continue
        x1, y1, x2, y2 = block_bbox
        bbox = [x1 / page_width, y1 / page_height, x2 / page_width, y2 / page_height]
        if bbox[0] < bbox[2] and bbox[1] < bbox[3]:
            blocks.append(ContentBlock("text", bbox, content="\n".join(texts)))

    if native_chars < min_chars or not blocks:
        return None
    return blocks


def native_text_layouts_from_document(
    pdf_doc: Any,
    page_indices: Sequence[int],
    min_chars: int,
) -> list[list[ContentBlock] | None]:
    return [native_text_layout(pdf_doc[index], min_chars) for index in page_indices]


def native_text_layouts_from_pdf_bytes(
    pdf_bytes: bytes,
    page_indices: Sequence[int],
    min_chars: int,
) -> list[list[ContentBlock] | None]:
    pdf_doc = open_pdfium_document(pdfium.PdfDocument, pdf_bytes)
    try:
        return native_text_layouts_from_document(pdf_doc, page_indices, min_chars)
    finally:
        close_pdfium_document(pdf_doc)


def _extract_with_page_layouts(
    predictor: Any,
    images: list[Any],
    native_layouts: Sequence[list[ContentBlock] | None],
    *,
    image_analysis: bool | None = None,
) -> list[Any]:
    if len(images) != len(native_layouts):
        raise RuntimeError("native layout count does not match page count")

    results: list[Any] = [None] * len(images)
    native_positions = [index for index, blocks in enumerate(native_layouts) if blocks]
    remote_positions = [index for index, blocks in enumerate(native_layouts) if not blocks]

    if native_positions:
        native_results = predictor.batch_extract_with_layout(
            [images[index] for index in native_positions],
            [native_layouts[index] for index in native_positions],
            not_extract_list=["text"],
            image_analysis=image_analysis,
        )
        for index, result in zip(native_positions, native_results):
            results[index] = result

    if remote_positions:
        remote_results = batch_extract_with_bbox_json_layout(
            predictor,
            [images[index] for index in remote_positions],
            image_analysis=image_analysis,
        )
        for index, result in zip(remote_positions, remote_results):
            results[index] = result

    logger.info(
        "Native text fast path: {} pages local, {} pages remote",
        len(native_positions),
        len(remote_positions),
    )
    return results


def batch_extract_with_native_text_fallback(
    predictor: Any,
    images: list[Any],
    pdf_doc: Any,
    page_start_index: int,
    min_chars: int,
    *,
    image_analysis: bool | None = None,
) -> list[Any]:
    page_indices = list(range(page_start_index, page_start_index + len(images)))
    native_layouts = native_text_layouts_from_document(pdf_doc, page_indices, min_chars)
    return _extract_with_page_layouts(
        predictor,
        images,
        native_layouts,
        image_analysis=image_analysis,
    )


async def aio_batch_extract_with_native_text_fallback(
    predictor: Any,
    images: list[Any],
    pdf_bytes: bytes,
    page_start_index: int,
    min_chars: int,
    *,
    semaphore: Any = None,
    image_analysis: bool | None = None,
) -> list[Any]:
    import asyncio

    page_indices = list(range(page_start_index, page_start_index + len(images)))
    native_layouts = await asyncio.to_thread(
        native_text_layouts_from_pdf_bytes,
        pdf_bytes,
        page_indices,
        min_chars,
    )
    native_positions = [index for index, blocks in enumerate(native_layouts) if blocks]
    remote_positions = [index for index, blocks in enumerate(native_layouts) if not blocks]
    results: list[Any] = [None] * len(images)

    if native_positions:
        native_results = await predictor.aio_batch_extract_with_layout(
            [images[index] for index in native_positions],
            [native_layouts[index] for index in native_positions],
            semaphore=semaphore,
            not_extract_list=["text"],
            image_analysis=image_analysis,
        )
        for index, result in zip(native_positions, native_results):
            results[index] = result

    if remote_positions:
        remote_results = await aio_batch_extract_with_bbox_json_layout(
            predictor,
            [images[index] for index in remote_positions],
            semaphore=semaphore,
            image_analysis=image_analysis,
        )
        for index, result in zip(remote_positions, remote_results):
            results[index] = result

    logger.info(
        "Native text fast path: {} pages local, {} pages remote",
        len(native_positions),
        len(remote_positions),
    )
    return results


def _layout_request(predictor: Any, images: list[Any]) -> tuple[list[Any], str, Any]:
    layout_images = predictor.helper.batch_prepare_for_layout(None, images)
    prompt = MULTIMODAL_LAYOUT_PROMPT
    params = predictor.sampling_params.get("[layout]") or predictor.sampling_params.get("[default]")
    if params is not None and MULTIMODAL_LAYOUT_MAX_TOKENS:
        if hasattr(params, "max_new_tokens"):
            if is_dataclass(params):
                params = replace(params, max_new_tokens=MULTIMODAL_LAYOUT_MAX_TOKENS)
            else:
                try:
                    params = copy(params)
                    params.max_new_tokens = MULTIMODAL_LAYOUT_MAX_TOKENS
                except (AttributeError, TypeError):
                    logger.warning("Unable to set layout max_new_tokens; using client defaults")
    return layout_images, prompt, params


def batch_extract_with_bbox_json_layout(
    predictor: Any,
    images: list[Any],
    *,
    image_analysis: bool | None = None,
) -> list[Any]:
    """Run JSON layout detection, then reuse MinerU's normal post-processing."""
    layout_images, prompt, params = _layout_request(predictor, images)
    outputs = predictor.client.batch_predict(layout_images, prompt, params)
    blocks_list = [parse_bbox_json_layout(output) for output in outputs]
    if len(blocks_list) != len(images):
        raise RuntimeError("layout response count does not match page count")

    logger.info("External JSON layout adapter detected {} blocks on {} pages", sum(map(len, blocks_list)), len(images))
    return predictor.batch_extract_with_layout(
        images,
        blocks_list,
        not_extract_list=["text"],
        image_analysis=image_analysis,
    )


async def aio_batch_extract_with_bbox_json_layout(
    predictor: Any,
    images: list[Any],
    *,
    semaphore: Any = None,
    image_analysis: bool | None = None,
) -> list[Any]:
    """Async counterpart of :func:`batch_extract_with_bbox_json_layout`."""
    layout_images, prompt, params = _layout_request(predictor, images)
    outputs = await predictor.client.aio_batch_predict(
        layout_images,
        prompt,
        params,
        semaphore=semaphore,
    )
    blocks_list = [parse_bbox_json_layout(output) for output in outputs]
    if len(blocks_list) != len(images):
        raise RuntimeError("layout response count does not match page count")

    logger.info("External JSON layout adapter detected {} blocks on {} pages", sum(map(len, blocks_list)), len(images))
    return await predictor.aio_batch_extract_with_layout(
        images,
        blocks_list,
        semaphore=semaphore,
        not_extract_list=["text"],
        image_analysis=image_analysis,
    )
