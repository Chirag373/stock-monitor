from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

# ==========================
#  WATCHLIST MODELS
# ==========================


class StockWatchRequest(BaseModel):
    symbol: str = Field(..., example="AAPL", description="Stock ticker symbol")
    dma_period: int = Field(
        ..., example=50, description="Moving Average Period (50, 100, 200)"
    )
    alert_threshold: float = Field(
        ..., ge=0.0, example=5.0, description="Alert threshold %"
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("dma_period")
    @classmethod
    def validate_dma(cls, v: int) -> int:
        if v not in (50, 100, 200):
            raise ValueError("dma_period must be 50, 100, or 200")
        return v


class StockWatchResponse(StockWatchRequest):
    last_price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    company_name: Optional[str] = None
    last_checked: Optional[datetime] = None


# ==========================
#  LOGS / ALERTS MODELS
# ==========================


class LogResponse(BaseModel):
    id: int
    timestamp: datetime
    symbol: str
    message: str
    alert_type: str = "INFO"


# ==========================
#  CHART DATA (For React Native UI)
# ==========================


class ChartDataPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    dma50: Optional[float] = None
    dma100: Optional[float] = None
    dma200: Optional[float] = None
