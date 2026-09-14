FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 libxcb1 \
    && rm -rf /var/lib/apt/lists/*
COPY document-parser/pyproject.toml document-parser/README.md document-parser/LICENSE.md /app/
COPY document-parser/mineru /app/mineru
# The API server itself does not need the optional local OCR/PyTorch pipeline.
# Keep the demo image CPU-friendly; model-backed parsing can use the configured
# remote multimodal endpoint through the backend.
RUN python -m pip install --no-cache-dir -e .

EXPOSE 8002
CMD ["mineru-api", "--host", "0.0.0.0", "--port", "8002"]
