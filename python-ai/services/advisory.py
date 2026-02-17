from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def advice_from_forecast(forecast: List[Dict[str, Any]]) -> Dict[str, Any]:
  """
  Takes a list of forecast entries with keys:
  - date (ISO string)
  - pop (probability of precipitation, 0-100)
  - rain (mm)
  - tempMax (°C)

  Returns low-literacy EN + SW guidance.
  """
  if not forecast:
    return {
        "action": "watch",
        "text_en": "Keep watching the weather. No update available.",
        "text_sw": "Endelea kufuatilia hali ya hewa. Hakuna taarifa kwa sasa.",
        "icon": "eye",
    }

  next_days = forecast[:3]
  pop_high = all((day.get("pop", 0) or 0) >= 60 for day in next_days)
  temp_ok = all((day.get("tempMax", 0) or 0) <= 30 for day in next_days)

  if pop_high and temp_ok:
    return {
        "action": "plant",
        "text_en": "Good to plant next 3 days. Light rain is coming.",
        "text_sw": "Ni vizuri kupanda siku 3 zijazo. Mvua nyepesi inakuja.",
        "icon": "seedling",
    }

  next_two = forecast[:2]
  harvest_block = any((day.get("pop", 0) or 0) >= 50 for day in next_two)
  if harvest_block:
    for idx in range(len(forecast) - 1):
      today = forecast[idx]
      tomorrow = forecast[idx + 1]
      if (today.get("pop", 100) < 40) and (tomorrow.get("pop", 100) < 40):
        target = datetime.fromisoformat(today["date"]).strftime("%A")
        return {
            "action": "wait",
            "text_en": f"Hold harvest. Try from {target} when skies clear.",
            "text_sw": f"Subiri kuvuna. Anza {target} wakati anga itatulia.",
            "icon": "umbrella",
        }

    return {
        "action": "wait",
        "text_en": "Wait to harvest. Rain likely soon.",
        "text_sw": "Subiri kuvuna. Mvua inatarajiwa karibuni.",
        "icon": "umbrella",
    }

  return {
      "action": "watch",
      "text_en": "No major weather alerts. Keep daily checks.",
      "text_sw": "Hakuna tahadhari kubwa. Endelea kukagua kila siku.",
      "icon": "eye",
  }

