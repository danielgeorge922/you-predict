from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # GCP
    gcp_project_id: str
    gcp_region: str = "US"
    bq_dataset: str = "you_predict_warehouse"
    gcs_raw_bucket: str = "you-predict-raw"
    gcs_model_bucket: str = "you-predict-models"

    # YouTube API
    youtube_api_key: str = ""

    # Cloud Tasks
    cloud_tasks_queue: str = "snapshot-fanout"
    cloud_tasks_location: str = "us-east1"
    cloud_run_service_url: str = ""

    # Monitoring
    monitoring_window_hours: int = 72

    model_config = {"env_file": ".env"}
