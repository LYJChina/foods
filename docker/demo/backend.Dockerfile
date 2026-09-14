FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt
COPY backend/ /app/

EXPOSE 8001
CMD ["uvicorn", "app:create_app", "--factory", "--lifespan", "off", "--host", "0.0.0.0", "--port", "8001"]
