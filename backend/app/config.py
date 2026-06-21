from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    GEMINI_API_KEY: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FRONTEND_URL: str = "http://localhost:3000"
    # SEC's fair-access policy (https://www.sec.gov/os/webmaster-faq#developers)
    # requires a descriptive User-Agent identifying the requester on every
    # data.sec.gov / www.sec.gov call -- not a secret, just a courtesy
    # identifier. Defaulted (not required) so existing deployments don't break
    # on this new var; operators should override with a real contact.
    SEC_EDGAR_USER_AGENT: str = "SentinelIQ research contact@sentineliq.io"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
