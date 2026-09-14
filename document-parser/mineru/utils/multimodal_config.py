"""Environment-backed configuration for the HTTP multimodal client."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _integer(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    return int(value) if value else default


MULTIMODAL_API_URL = os.getenv("MULTIMODAL_API_URL", "").strip()
MULTIMODAL_MODEL = os.getenv("MULTIMODAL_MODEL", "").strip()
MULTIMODAL_API_KEY = os.getenv("MULTIMODAL_API_KEY", "").strip()
MULTIMODAL_TIMEOUT = _integer("MULTIMODAL_TIMEOUT", 120)
MULTIMODAL_MAX_CONCURRENCY = _integer("MULTIMODAL_MAX_CONCURRENCY", 2)
MULTIMODAL_LAYOUT_MAX_TOKENS = _integer("MULTIMODAL_LAYOUT_MAX_TOKENS", 8192)
PDF_NATIVE_TEXT_MIN_CHARS = _integer("PDF_NATIVE_TEXT_MIN_CHARS", 80)
PDF_NATIVE_TEXT_FAST_PATH = os.getenv("PDF_NATIVE_TEXT_FAST_PATH", "true").lower() not in {
    "0",
    "false",
    "no",
}
MULTIMODAL_LAYOUT_PROMPT = """
Analyze this document page as an OCR engine and return ONLY a compact JSON array.
Each text region MUST be one object with these keys:
{"bbox_2d":[xmin,ymin,xmax,ymax],"text_content":"exact text","confidence":0.0,"char_boxes":[[char,xmin,ymin,xmax,ymax,confidence]]}
Coordinates are integers in the 0-1000 page coordinate system. Confidence is a number in [0,1].
char_boxes MUST contain one compact six-item array per non-whitespace character, in reading order:
[the exact one-character string, xmin, ymin, xmax, ymax, confidence].
Use [] only if character boxes genuinely cannot be determined. Keep all JSON on one line where possible.
Preserve text exactly, including line breaks and Markdown table syntax. Do not include whitespace entries in char_boxes.
Do not describe the image, add explanations, use Markdown fences, or return any key other than the four specified keys.
Do not omit readable text regions. Return [] when no readable content is present.
""".strip()
MULTIMODAL_SKIP_MODEL_NAME_CHECKING = True


@dataclass(frozen=True)
class FixedHttpClientSettings:
    server_url: str
    model_name: str
    server_headers: dict[str, str]
    http_timeout: int
    max_concurrency: int
    skip_model_name_checking: bool


def get_fixed_http_client_settings() -> FixedHttpClientSettings:
    if not MULTIMODAL_API_URL:
        raise ValueError("MULTIMODAL_API_URL must be configured for the HTTP VLM client")
    if not MULTIMODAL_MODEL:
        raise ValueError("MULTIMODAL_MODEL must be configured for the HTTP VLM client")

    headers: dict[str, str] = {}
    if MULTIMODAL_API_KEY:
        headers["Authorization"] = f"Bearer {MULTIMODAL_API_KEY}"

    return FixedHttpClientSettings(
        server_url=MULTIMODAL_API_URL,
        model_name=MULTIMODAL_MODEL,
        server_headers=headers,
        http_timeout=MULTIMODAL_TIMEOUT,
        max_concurrency=MULTIMODAL_MAX_CONCURRENCY,
        skip_model_name_checking=MULTIMODAL_SKIP_MODEL_NAME_CHECKING,
    )
