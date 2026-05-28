# Optimized for Render free tier: slim image, single process, low memory footprint
FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TORCH_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    TOKENIZERS_PARALLELISM=false

# Render sets PORT at runtime (default 10000)
ENV PORT=10000

COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Bake model weights into the image so cold starts skip Hugging Face downloads
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" \
    && python -c "from transformers import AutoModelForSequenceClassification, AutoTokenizer; m='textattack/distilbert-base-uncased-CoLA'; AutoTokenizer.from_pretrained(m); AutoModelForSequenceClassification.from_pretrained(m)"

COPY app ./app

EXPOSE 10000

# One worker keeps RAM usage low on the free tier
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
