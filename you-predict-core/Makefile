PROJECT  = you-predict-483316
REGION   = us-east1
SERVICE  = you-predict-core
SA       = you-predict-master-account@you-predict-483316.iam.gserviceaccount.com

dev:
	uv run uvicorn main:app --reload --port 8080

test:
	uv run pytest tests/

lint:
	uv run ruff check src/ tests/

fmt:
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/


deploy:
	gcloud run deploy $(SERVICE) --source . --region=$(REGION) --service-account=$(SA) --allow-unauthenticated --port=8080

# ── ops ────────────────────────────────────────────────────────────────────────

logs:
	gcloud beta run services logs tail $(SERVICE) --region=$(REGION)

logs-history:
	gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$(SERVICE)" --project=$(PROJECT) --limit=200 --order=desc --format="table(timestamp,httpRequest.status,httpRequest.requestUrl,textPayload)"

seed-channels:
	uv run python -m src.scripts.seed_tracked_channels

subscribe:
	uv run python -m src.scripts.subscribe_channels

seed-and-subscribe:
	uv run python -m src.scripts.seed_tracked_channels
	uv run python -m src.scripts.subscribe_channels

renew-scheduler:
	gcloud scheduler jobs create http renew-subscriptions --location=$(REGION) --schedule="0 0 */4 * *" --uri="https://you-predict-core-2n75rmagqa-ue.a.run.app/pipelines/renew-subscriptions" --http-method=POST --oidc-service-account-email=$(SA) --oidc-token-audience="https://you-predict-core-2n75rmagqa-ue.a.run.app"

bootstrap:
	uv run python -m src.scripts.bootstrap_all

.PHONY: dev test lint fmt typecheck deploy logs seed-channels subscribe seed-and-subscribe renew-scheduler bootstrap
