from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

from services.price_model import PriceModelStore, train_price_model, predict_price
from services.yield_model import (
    predict_crop_yield,
    predict_livestock_yield,
)
from services.advisory import advice_from_forecast


app = FastAPI(title="GreenVast AI Service", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PRICE_MODEL_STORE = PriceModelStore()


class PriceSnapshot(BaseModel):
    commodity: str
    market: str
    date: datetime
    unit: str = "kg"
    minPrice: Optional[float] = None
    maxPrice: Optional[float] = None
    avgPrice: Optional[float] = None
    medianPrice: Optional[float] = None


class TrainPriceRequest(BaseModel):
    rows: List[PriceSnapshot]


class PricePredictRequest(BaseModel):
    commodity: str
    market: str
    date: Optional[datetime] = None

    @validator("commodity", "market")
    def _strip(cls, value: str) -> str:
        return value.strip()


class YieldHistoryItem(BaseModel):
    season: Optional[str] = None
    quantity: float = Field(gt=0)
    unit: Optional[str] = None
    areaHa: Optional[float] = Field(default=None, gt=0)


class YieldCropRequest(BaseModel):
    crop: str
    areaHa: float = Field(gt=0)
    county: str
    subCounty: Optional[str] = None
    history: List[YieldHistoryItem] = Field(default_factory=list)
    rainfall: Optional[float] = Field(default=None, ge=0)
    outbreakRisk: Optional[float] = Field(default=0, ge=0, le=1)


class YieldLivestockRequest(BaseModel):
    type: Literal["Dairy", "Beef"]
    headCount: int = Field(gt=0)
    sessionsPerDay: Optional[int] = Field(default=2, gt=0, le=6)
    avgMilkLpd: Optional[float] = Field(default=None, gt=0)
    droughtRisk: Optional[float] = Field(default=0, ge=0, le=1)
    outbreakRisk: Optional[float] = Field(default=0, ge=0, le=1)
    history: Optional[List[Dict[str, Any]]] = None


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": "python-ai", "version": app.version}


@app.post("/train/price")
def train_price(request: TrainPriceRequest) -> Dict[str, Any]:
    if not request.rows:
        raise HTTPException(status_code=400, detail="rows must not be empty")

    report = train_price_model(PRICE_MODEL_STORE, request.rows)
    return report


@app.post("/predict/price")
def predict_price_endpoint(request: PricePredictRequest) -> Dict[str, Any]:
    result = predict_price(PRICE_MODEL_STORE, request.commodity, request.market, request.date)
    if result is None:
        raise HTTPException(status_code=404, detail="No price history for commodity/market pair")
    return result


@app.post("/predict/yield/crop")
def predict_yield_crop(request: YieldCropRequest) -> Dict[str, Any]:
    return predict_crop_yield(request.dict())


@app.post("/predict/yield/livestock")
def predict_yield_livestock(request: YieldLivestockRequest) -> Dict[str, Any]:
    return predict_livestock_yield(request.dict())


@app.post("/advisory")
def advisory_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    # payload is expected to include forecast data (probability, rain, temperature)
    forecast = payload.get("forecast", [])
    return advice_from_forecast(forecast)

