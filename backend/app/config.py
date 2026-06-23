from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# CLAUDE.md / .env.example document this minimum (SECRET_KEY=your_secret_key_minimum_32_chars)
# but nothing previously enforced it (S-1) -- a short key makes every HS256 JWT forgeable.
MIN_SECRET_KEY_LENGTH = 32

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

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if len(v) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters "
                f"(got {len(v)}) -- a short key makes every JWT forgeable."
            )
        return v

settings = Settings()
