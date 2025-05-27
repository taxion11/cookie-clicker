# ============================================================================
# Cookie Clicker Game - Development Makefile
# ============================================================================

.PHONY: help setup build run stop clean test deploy logs

# デフォルトターゲット
.DEFAULT_GOAL := help

# 色付きヘルプ
BOLD=\033[1m
RESET=\033[0m
BLUE=\033[34m
GREEN=\033[32m
YELLOW=\033[33m

# ============================================================================
# ヘルプとセットアップ
# ============================================================================

help: ## 📋 使用可能なコマンドを表示
	@echo "$(BOLD)Cookie Clicker Game - Development Commands$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(BLUE)%-15s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

setup: ## 🚀 プロジェクトの初期セットアップ
	@echo "$(BOLD)Setting up Cookie Clicker development environment...$(RESET)"
	@docker --version || (echo "❌ Docker is required" && exit 1)
	@docker compose version || (echo "❌ Docker Compose is required" && exit 1)
	@echo "✅ Docker environment verified"
	@mkdir -p go-app/static/{css,js,images}
	@mkdir -p go-app/templates
	@mkdir -p python-api/{app,tests,alembic}
	@mkdir -p sql nginx/conf.d logs
	@echo "✅ Directory structure created"
	@echo "$(GREEN)Setup completed! Run 'make run' to start development.$(RESET)"

# ============================================================================
# 開発環境管理
# ============================================================================

build: ## 🔨 全サービスをビルド
	@echo "$(BOLD)Building all services...$(RESET)"
	@docker compose build --parallel
	@echo "$(GREEN)Build completed!$(RESET)"

run: ## ▶️  開発環境を起動
	@echo "$(BOLD)Starting development environment...$(RESET)"
	@docker compose up -d
	@echo "$(GREEN)Services started!$(RESET)"
	@echo ""
	@echo "🌐 Go Frontend:     http://localhost:8080"
	@echo "🐍 Python API:     http://localhost:8001"
	@echo "📊 API Docs:       http://localhost:8001/docs"
	@echo "🗄️  PostgreSQL:     localhost:5432"
	@echo "🔴 Redis:          localhost:6379"
	@echo ""

run-prod: ## 🚀 本番環境モードで起動
	@echo "$(BOLD)Starting production environment...$(RESET)"
	@docker compose --profile production up -d
	@echo "$(GREEN)Production environment started!$(RESET)"

stop: ## ⏹️  全サービスを停止
	@echo "$(BOLD)Stopping all services...$(RESET)"
	@docker compose down
	@echo "$(GREEN)Services stopped!$(RESET)"

restart: stop run ## 🔄 サービスを再起動

# ============================================================================
# 開発ツール
# ============================================================================

logs: ## 📜 全サービスのログを表示
	@docker compose logs -f

logs-go: ## 📜 Goアプリのログを表示
	@docker compose logs -f go-app

logs-python: ## 📜 Python APIのログを表示
	@docker compose logs -f python-api

logs-db: ## 📜 データベースのログを表示
	@docker compose logs -f postgres

shell-go: ## 🐚 Goコンテナに接続
	@docker compose exec go-app sh

shell-python: ## 🐚 Python APIコンテナに接続
	@docker compose exec python-api bash

shell-db: ## 🐚 PostgreSQLに接続
	@docker compose exec postgres psql -U postgres -d cookie_clicker

# ============================================================================
# テストとコード品質
# ============================================================================

test: ## 🧪 全テストを実行
	@echo "$(BOLD)Running all tests...$(RESET)"
	@make test-go
	@make test-python

test-go: ## 🧪 Goテストを実行
	@echo "$(BOLD)Running Go tests...$(RESET)"
	@docker compose exec go-app go test -v ./...

test-python: ## 🧪 Pythonテストを実行
	@echo "$(BOLD)Running Python tests...$(RESET)"
	@docker compose exec python-api pytest -v

lint: ## 🔍 コード品質チェック
	@echo "$(BOLD)Running linting...$(RESET)"
	@make lint-go
	@make lint-python

lint-go: ## 🔍 Go コード品質チェック
	@echo "$(YELLOW)Linting Go code...$(RESET)"
	@docker compose exec go-app go fmt ./...
	@docker compose exec go-app go vet ./...

lint-python: ## 🔍 Python コード品質チェック
	@echo "$(YELLOW)Linting Python code...$(RESET)"
	@docker compose exec python-api black --check .
	@docker compose exec python-api flake8 .
	@docker compose exec python-api mypy .

format: ## ✨ コードフォーマット
	@echo "$(BOLD)Formatting code...$(RESET)"
	@docker compose exec go-app go fmt ./...
	@docker compose exec python-api black .
	@docker compose exec python-api isort .

# ============================================================================
# データベース管理
# ============================================================================

db-migrate: ## 🗄️ データベースマイグレーション実行
	@echo "$(BOLD)Running database migrations...$(RESET)"
	@docker compose exec python-api alembic upgrade head

db-migration: ## 🗄️ 新しいマイグレーションファイル作成
	@read -p "Migration name: " name; \
	docker compose exec python-api alembic revision --autogenerate -m "$$name"

db-reset: ## 🗄️ データベースをリセット
	@echo "$(YELLOW)⚠️  This will delete all data!$(RESET)"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker compose down -v; \
		docker volume prune -f; \
		docker compose up -d postgres; \
		echo "$(GREEN)Database reset completed!$(RESET)"; \
	fi

db-backup: ## 💾 データベースバックアップ
	@echo "$(BOLD)Creating database backup...$(RESET)"
	@mkdir -p backups
	@docker compose exec postgres pg_dump -U postgres cookie_clicker > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup created in backups/ directory$(RESET)"

# ============================================================================
# 本番環境とデプロイ
# ============================================================================

build-prod: ## 🏗️ 本番用イメージをビルド
	@echo "$(BOLD)Building production images...$(RESET)"
	@docker compose -f docker-compose.yml -f docker-compose.prod.yml build

deploy-staging: ## 🚀 ステージング環境にデプロイ
	@echo "$(BOLD)Deploying to staging...$(RESET)"
	@echo "$(YELLOW)This would trigger GitHub Actions deployment$(RESET)"

deploy-prod: ## 🚀 本番環境にデプロイ
	@echo "$(BOLD)Deploying to production...$(RESET)"
	@echo "$(YELLOW)This would trigger GitHub Actions deployment$(RESET)"

# ============================================================================
# クリーンアップ
# ============================================================================

clean: ## 🧹 開発環境をクリーンアップ
	@echo "$(BOLD)Cleaning up development environment...$(RESET)"
	@docker compose down -v --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)Cleanup completed!$(RESET)"

clean-all: ## 🧹 全Dockerリソースを削除
	@echo "$(YELLOW)⚠️  This will remove ALL Docker resources!$(RESET)"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker compose down -v --remove-orphans; \
		docker system prune -a -f --volumes; \
		echo "$(GREEN)All Docker resources removed!$(RESET)"; \
	fi

# ============================================================================
# 開発ユーティリティ
# ============================================================================

status: ## 📊 サービス状態を確認
	@echo "$(BOLD)Service Status:$(RESET)"
	@docker compose ps

health: ## 🏥 サービスヘルスチェック
	@echo "$(BOLD)Health Check:$(RESET)"
	@echo "Go App:     $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null || echo "DOWN")"
	@echo "Python API: $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "DOWN")"

install-go-deps: ## 📦 Go依存関係をインストール
	@docker compose exec go-app go mod tidy
	@docker compose exec go-app go mod download

install-python-deps: ## 📦 Python依存関係をインストール
	@docker compose exec python-api pip install -r requirements.txt

update-deps: ## 📦 全依存関係を更新
	@make install-go-deps
	@make install-python-deps

# ============================================================================
# 情報表示
# ============================================================================

info: ## ℹ️  プロジェクト情報を表示
	@echo "$(BOLD)Cookie Clicker Game Development Environment$(RESET)"
	@echo ""
	@echo "📁 Project Structure:"
	@echo "   go-app/          - Go Gin frontend"
	@echo "   python-api/      - Python FastAPI backend"
	@echo "   sql/             - Database scripts"
	@echo "   nginx/           - Nginx configuration"
	@echo ""
	@echo "🔧 Quick Start:"
	@echo "   make setup       - Initialize project"
	@echo "   make run         - Start development"
	@echo "   make logs        - View logs"
	@echo "   make test        - Run tests"
	@echo ""

urls: ## 🌐 重要なURLを表示
	@echo "$(BOLD)Development URLs:$(RESET)"
	@echo "🌐 Frontend:       http://localhost:8080"
	@echo "🐍 API:           http://localhost:8001"
	@echo "📖 API Docs:      http://localhost:8001/docs"
	@echo "📊 API Redoc:     http://localhost:8001/redoc"