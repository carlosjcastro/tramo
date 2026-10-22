FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 FASTEMBED_CACHE_PATH=/models PORT=7860
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')"
COPY app app
RUN useradd -m tramo && chown -R tramo /models
USER tramo
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port ${PORT}"]
