# ============================================================================
# Python FastAPI Dockerfile
# ============================================================================

FROM python:3.12-slim

# 環境変数設定
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# システムパッケージ更新とクリーンアップ
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        wget \
        curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 非rootユーザー作成
RUN groupadd -r appgroup && \
    useradd -r -g appgroup appuser

# 作業ディレクトリ設定
WORKDIR /app

# 要件ファイルをコピーして依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# ディレクトリ所有権変更
RUN chown -R appuser:appgroup /app

# 非rootユーザーに切り替え
USER appuser

# ポート公開
EXPOSE 8001

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# アプリケーション実行
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]