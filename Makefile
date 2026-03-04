.PHONY: setup dev test ingest lint clean api web

setup:
	@echo "Setting up Vitalytics..."
	cp -n .env.example .env 2>/dev/null || true
	python3 -m venv .venv || true
	.venv/bin/pip install -r apps/api/requirements.txt
	cd apps/web && pnpm install
	@echo "Setup complete! Activate venv with: source .venv/bin/activate"

dev:
	@echo "Starting Vitalytics development servers..."
	@trap 'kill 0' EXIT; \
	.venv/bin/uvicorn apps.api.app.main:app --reload --port 8002 & \
	cd apps/web && pnpm dev & \
	wait

api:
	.venv/bin/uvicorn apps.api.app.main:app --reload --port 8002

web:
	cd apps/web && pnpm dev

test:
	.venv/bin/python -m pytest apps/api/tests/ -v

ingest:
	.venv/bin/python scripts/ingest_harrison.py

seed:
	.venv/bin/python scripts/seed_data.py

lint:
	.venv/bin/ruff check apps/api/ || true
	cd apps/web && pnpm lint || true

deploy-check:
	@echo "=== Deployment Readiness Check ==="
	@echo ""
	@echo "--- Frontend (Vercel) ---"
	@test -f apps/web/.env.local && echo "  .env.local exists" || echo "  WARNING: apps/web/.env.local missing"
	@cd apps/web && npx next build && echo "  Build: PASS" || echo "  Build: FAIL"
	@echo ""
	@echo "--- Backend (DigitalOcean) ---"
	@test -f .env && echo "  .env exists" || echo "  WARNING: .env missing"
	@curl -sf http://localhost:8002/health > /dev/null 2>&1 && echo "  Health check: PASS" || echo "  Health check: SKIP (server not running)"
	@echo ""
	@echo "=== Done ==="

clean:
	rm -rf apps/api/data/chroma_db
	rm -rf apps/api/data/analyses
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf apps/web/.next
	@echo "Cleaned."
