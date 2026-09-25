# ============================================================
# TuneMatch 常用命令
# ============================================================
.PHONY: backend frontend install seed test test-backend test-frontend build dev

install: ## 安装前后端依赖
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

seed: ## 导入曲库（SQLite + ChromaDB）
	cd backend && python ../scripts/init_library.py

backend: ## 启动后端（http://localhost:8000）
	cd backend && uvicorn main:app --reload --port 8000

frontend: ## 启动前端（http://localhost:5173）
	cd frontend && npm run dev

dev: backend frontend ## 前后端同时启动（两个终端）

test-backend: ## 后端测试
	cd backend && pytest tests/ -v

test-frontend: ## 前端测试
	cd frontend && npm run test

build: ## 前端生产构建
	cd frontend && npm run build
