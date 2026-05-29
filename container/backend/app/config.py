from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gcp_project_id: str = Field(default="", alias="GCP_PROJECT_ID")
    gcs_bucket: str = Field(default="", alias="GCS_BUCKET")
    apps_script_url: str = Field(default="", alias="APPS_SCRIPT_URL")
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    dashboard_password: str = Field(default="", alias="DASHBOARD_PASSWORD")
    teams_reminder_webhook: str = Field(default="", alias="TEAMS_REMINDER_WEBHOOK")
    sheets_url: str = Field(default="", alias="SHEETS_URL")

    model_config = SettingsConfigDict(env_file=("config.env", "../config.env"), extra="ignore")

settings = Settings()
