from pydantic import BaseModel


class RateLimitRule(BaseModel):
    window_hours: int
    limit: int
