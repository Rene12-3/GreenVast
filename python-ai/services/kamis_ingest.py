from __future__ import annotations

from typing import Iterable, List, Dict, Any
from datetime import datetime


def normalise_snapshots(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
  """
  Accepts raw JSON-like snapshots and normalises keys used by the price model.
  Intended for development-time ingestion; no network IO.
  """
  normalised = []
  for row in rows:
    try:
      normalised.append(
          {
              "commodity": str(row["commodity"]),
              "market": str(row["market"]),
              "date": datetime.fromisoformat(str(row["date"])),
              "unit": row.get("unit", "kg"),
              "minPrice": row.get("minPrice"),
              "maxPrice": row.get("maxPrice"),
              "avgPrice": row.get("avgPrice"),
              "medianPrice": row.get("medianPrice"),
          }
      )
    except (KeyError, ValueError):
      continue
  return normalised

