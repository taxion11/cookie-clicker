# Simple Go Dockerfile for development
FROM golang:1.21-alpine

# 必要なパッケージをインストール
RUN apk add --no-cache git ca-certificates

# 作業ディレクトリ設定
WORKDIR /app

# Go modules ファイルをコピー
COPY go.mod go.sum ./

# 依存関係ダウンロード
RUN go mod download

# ソースコードをコピー
COPY . .

# アプリケーションをビルド
RUN go build -o cookie-clicker-app .

# ポート公開
EXPOSE 8080

# アプリケーション実行
CMD ["./cookie-clicker-app"]