from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np


PairKey = Tuple[str, str]


@dataclass
class PricePoint:
  date: datetime
  price: float
  unit: str


class PriceModelStore:
  """
  In-memory registry for trained price baselines.
  Persists for the lifetime of the Python process.
  """

  def __init__(self) -> None:
    self.models: Dict[PairKey, Dict[str, object]] = {}
    self.version = "v0.1"
    self.trained_at: Optional[datetime] = None

  def clear(self) -> None:
    self.models.clear()
    self.trained_at = None


def _normalise_price(row) -> Optional[float]:
  candidates = [
      row.avgPrice,
      row.medianPrice,
      np.nanmean([row.minPrice, row.maxPrice]) if row.minPrice and row.maxPrice else None,
  ]
  for value in candidates:
    if value is not None and value > 0:
      return float(value)
  return None


def train_price_model(store: PriceModelStore, rows: Iterable) -> Dict[str, object]:
  grouped: Dict[PairKey, List[PricePoint]] = defaultdict(list)

  for row in rows:
    price = _normalise_price(row)
    if price is None:
      continue
    key = (row.commodity.lower(), row.market.lower())
    grouped[key].append(PricePoint(date=row.date, price=price, unit=row.unit))

  for key, points in grouped.items():
    ordered = sorted(points, key=lambda p: p.date)
    prices = np.array([p.price for p in ordered], dtype=float)
    weeks = np.arange(len(prices), dtype=float)

    # Simple linear trend fit; robust to small sample sizes.
    slope = 0.0
    intercept = float(np.median(prices))
    if len(prices) >= 3 and np.ptp(prices) > 0:
      slope, intercept = np.polyfit(weeks, prices, 1)

    rolling = float(np.median(prices[-3:])) if len(prices) >= 3 else float(prices[-1])
    recent_unit = ordered[-1].unit

    store.models[key] = {
        "prices": ordered,
        "trend": {"slope": float(slope), "intercept": float(intercept)},
        "rollingMedian": rolling,
        "unit": recent_unit,
        "count": len(prices),
    }

  store.trained_at = datetime.utcnow()
  return {
      "version": store.version,
      "pairs": len(store.models),
      "trainedAt": store.trained_at.isoformat() if store.trained_at else None,
  }


def predict_price(
    store: PriceModelStore,
    commodity: str,
    market: str,
    for_date: Optional[datetime],
) -> Optional[Dict[str, object]]:
  key = (commodity.lower(), market.lower())
  entry = store.models.get(key)
  if not entry:
    return None

  points: List[PricePoint] = entry["prices"]
  count = entry["count"]
  slope = entry["trend"]["slope"]
  intercept = entry["trend"]["intercept"]
  unit = entry["unit"]

  if for_date:
    # Estimate the step index relative to oldest sample.
    delta_days = (for_date - points[0].date).days
    weeks_ahead = max(delta_days / 7.0, 0)
  else:
    weeks_ahead = len(points) - 1

  trend_price = intercept + slope * weeks_ahead
  baseline = entry["rollingMedian"]
  price_estimate = (trend_price + baseline) / 2.0
  price_estimate = max(price_estimate, 0.01)

  variance = np.var([p.price for p in points]) if count > 1 else 0.0
  confidence = min(0.9, 0.35 + (count * 0.1) - (variance * 0.001))
  confidence = max(0.2, round(confidence, 2))

  low = round(price_estimate * 0.92, 2)
  high = round(price_estimate * 1.08, 2)

  return {
      "commodity": commodity,
      "market": market,
      "price": round(price_estimate, 2),
      "low": low,
      "high": high,
      "unit": unit,
      "confidence": confidence,
      "modelVersion": store.version,
      "trainedAt": store.trained_at.isoformat() if store.trained_at else None,
      "historyCount": count,
  }

