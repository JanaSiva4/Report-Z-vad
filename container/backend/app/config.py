from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gcp_project_id: str = Field(default="", alias="GCP_PROJECT_ID")
    gcs_bucket: str = Field(default="", alias="GCS_BUCKET")
    unify_api_url: str = Field(default="", alias="UNIFY_API_URL")
    unify_api_token: str = Field(default="", alias="UNIFY_API_TOKEN")
    unify_api_url_secret_name: str = Field(default="UNIFY_API_URL", alias="UNIFY_API_URL_SECRET_NAME")
    unify_api_token_secret_name: str = Field(default="UNIFY_API_TOKEN", alias="UNIFY_API_TOKEN_SECRET_NAME")
    unify_poll_seconds: int = Field(default=60, alias="UNIFY_POLL_SECONDS")
    apps_script_url: str = Field(default="", alias="APPS_SCRIPT_URL")
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    webhook_api_key: str = Field(default="", alias="WEBHOOK_API_KEY")
    dashboard_password: str = Field(default="", alias="DASHBOARD_PASSWORD")
    teams_reminder_webhook: str = Field(default="", alias="TEAMS_REMINDER_WEBHOOK")
    sheets_url: str = Field(default="", alias="SHEETS_URL")
    firestore_collection: str = Field(default="tickets", alias="FIRESTORE_COLLECTION")

    model_config = SettingsConfigDict(env_file=("config.env", "../config.env"), extra="ignore")

settings = Settings()
