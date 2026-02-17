from __future__ import annotations

from typing import Any, Dict, List, Optional


MODEL_VERSION = "v0.1"


IDEAL_RAINFALL_MM = 750.0
RAINFALL_BAND = 250.0


def _weighted_average(values: List[float]) -> float:
  if not values:
    return 0.0
  if len(values) == 1:
    return values[0]
  weights = list(range(1, len(values) + 1))
  numerator = sum(v * w for v, w in zip(values, weights))
  denominator = sum(weights)
  return numerator / denominator


def predict_crop_yield(payload: Dict[str, Any]) -> Dict[str, Any]:
  area = float(payload["areaHa"])
  history = payload.get("history", [])
  rainfall = payload.get("rainfall")
  outbreak_risk = payload.get("outbreakRisk") or 0.0

  per_ha_history: List[float] = []
  for record in history:
    qty = float(record["quantity"])
    if record.get("areaHa"):
      per_ha_history.append(qty / float(record["areaHa"]))
    else:
      per_ha_history.append(qty / max(area, 0.1))

  base_per_ha = _weighted_average(per_ha_history) or (2_000 / max(area, 0.1))
  base_output = base_per_ha * area

  rainfall_factor = 1.0
  if rainfall is not None:
    deviation = (rainfall - IDEAL_RAINFALL_MM) / RAINFALL_BAND
    rainfall_factor = max(0.7, min(1.2, 1.0 - 0.15 * deviation))

  risk_factor = max(0.6, 1.0 - outbreak_risk * 0.4)

  mid = base_output * rainfall_factor * risk_factor
  low = mid * 0.88
  high = mid * 1.12

  assumptions = [
      f"Base per-ha yield derived from {len(history) or 'synthetic'} season(s).",
      f"Rainfall adjustment factor: {rainfall_factor:.2f}.",
      f"Outbreak risk adjustment: {risk_factor:.2f}.",
  ]

  return {
      "low": round(low, 2),
      "mid": round(mid, 2),
      "high": round(high, 2),
      "unit": history[0]["unit"] if history and history[0].get("unit") else "kg",
      "assumptions": assumptions,
      "modelVersion": MODEL_VERSION,
  }


def predict_livestock_yield(payload: Dict[str, Any]) -> Dict[str, Any]:
  herd_type: str = payload["type"]
  head_count: int = int(payload["headCount"])
  drought_risk = payload.get("droughtRisk") or 0.0
  outbreak_risk = payload.get("outbreakRisk") or 0.0
  history = payload.get("history") or []

  risk_factor = max(0.6, 1.0 - drought_risk * 0.3 - outbreak_risk * 0.3)

  if herd_type == "Dairy":
    sessions = payload.get("sessionsPerDay") or 2
    avg_litre_per_cow = payload.get("avgMilkLpd")
    if avg_litre_per_cow is None:
      # infer from history (monthly totals)
      litres = [float(item.get("litres") or item.get("quantity") or 0) for item in history]
      days = max(len(litres), 1) * 30
      avg_litre_per_cow = (sum(litres) / max(days, 1)) / max(head_count, 1)
      avg_litre_per_cow = avg_litre_per_cow or 8.0

    base_daily = avg_litre_per_cow * head_count
    adjusted_daily = base_daily * risk_factor
    per_session = adjusted_daily / sessions

    return {
        "low": round(per_session * 0.9, 2),
        "mid": round(per_session, 2),
        "high": round(per_session * 1.1, 2),
        "unit": "litres_per_session",
        "assumptions": [
            f"Average milk per cow per day: {avg_litre_per_cow:.1f} L.",
            f"Sessions per day: {sessions}.",
            f"Risk adjustment factor: {risk_factor:.2f}.",
        ],
        "modelVersion": MODEL_VERSION,
    }

  if herd_type == "Beef":
    readiness_rate = 0.3
    if history:
      ready_counts = [
          float(item.get("headsReady") or item.get("quantity") or 0) for item in history
      ]
      readiness_rate = min(0.7, max(0.15, _weighted_average(ready_counts) / head_count))

    heads_ready = head_count * readiness_rate * risk_factor
    average_weight = (history[0].get("liveweightKg") if history and history[0].get("liveweightKg") else 320.0)
    mid_weight = average_weight * risk_factor

    return {
        "headsReady": round(heads_ready, 1),
        "liveweightKgRange": [
            round(mid_weight * 0.9, 1),
            round(mid_weight * 1.1, 1),
        ],
        "assumptions": [
            f"Base readiness rate: {readiness_rate:.2f}.",
            f"Risk adjustment factor: {risk_factor:.2f}.",
        ],
        "modelVersion": MODEL_VERSION,
    }

  raise ValueError(f"Unsupported livestock type: {herd_type}")

