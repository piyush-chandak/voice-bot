.PHONY: help infra backend agent frontend run stop

# ── colour helpers ────────────────────────────────────────────────────────────
BLUE  := \033[1;34m
GREEN := \033[1;32m
NC    := \033[0m

help:
	@echo ""
	@echo "  $(BLUE)voice-bot — developer commands$(NC)"
	@echo ""
	@echo "  $(GREEN)make infra$(NC)    — start LiveKit + Redis via Docker Compose"
	@echo "  $(GREEN)make stop$(NC)     — stop Docker Compose services"
	@echo "  $(GREEN)make backend$(NC)  — start FastAPI with hot-reload"
	@echo "  $(GREEN)make agent$(NC)    — start LiveKit voice-agent worker"
	@echo "  $(GREEN)make frontend$(NC) — start Vite dev server"
	@echo "  $(GREEN)make run$(NC)      — start backend + agent + frontend (3 panes)"
	@echo ""

# ── infrastructure ────────────────────────────────────────────────────────────
infra:
	@echo "$(BLUE)▶ Starting LiveKit + Redis…$(NC)"
	docker compose up -d

stop:
	@echo "$(BLUE)▶ Stopping services…$(NC)"
	docker compose down

# ── individual processes ──────────────────────────────────────────────────────
backend:
	@echo "$(BLUE)▶ Starting FastAPI backend on :8000…$(NC)"
	cd backend && PYTHONPATH=. .venv/bin/uvicorn app.main:app \
		--host 127.0.0.1 --port 8000 --reload

agent:
	@echo "$(BLUE)▶ Starting LiveKit voice-agent worker…$(NC)"
	cd backend && PYTHONPATH=. .venv/bin/python -m app.agents.livekit_agent dev

frontend:
	@echo "$(BLUE)▶ Starting Vite frontend on :5173…$(NC)"
	cd frontend && npm run dev

# ── combined dev target (requires iTerm2 / tmux / concurrently) ──────────────
run: infra
	@echo "$(BLUE)▶ Launching backend, agent and frontend in parallel…$(NC)"
	@command -v concurrently >/dev/null 2>&1 || npm install -g concurrently
	concurrently \
		--names "backend,agent,frontend" \
		--prefix-colors "blue,magenta,green" \
		"make backend" \
		"make agent" \
		"make frontend"
