import json
import logging

import httpx

from app.core.config import get_settings
from app.schemas.ranking import (
    RankingRequest,
    WorkshopRankingItem,
)

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


class RankingService:
    """Genera un ranking de talleres usando Claude como LLM."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def rank_workshops(self, payload: RankingRequest) -> list[WorkshopRankingItem]:
        """Llama a Claude y devuelve los talleres rankeados."""
        prompt = self._build_prompt(payload)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": self.settings.anthropic_model,
                    "max_tokens": 2048,
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()

        data = response.json()
        llm_text = data["content"][0]["text"]

        return self._parse_response(llm_text, payload)

    # ── Prompt ─────────────────────────────────────────────────────────────────

    def _build_prompt(self, payload: RankingRequest) -> str:
        req = payload.request_data
        workshops_json = json.dumps(
            [w.model_dump() for w in payload.workshops], ensure_ascii=False
        )

        return f"""Eres un experto en servicios mecánicos automotrices. Analiza la siguiente solicitud de servicio y los talleres disponibles, luego genera un ranking de los talleres más adecuados para atender esta solicitud.

## SOLICITUD DEL CLIENTE
- Descripción del problema: {req.description}
- Nivel de urgencia: {req.urgency}
- Tipo de problema: {req.problem_type}
- Vehículo: {req.vehicle_brand} {req.vehicle_model}
- Ubicación del cliente: Lat {req.latitude}, Lng {req.longitude}

## TALLERES DISPONIBLES
{workshops_json}

## INSTRUCCIONES
Para cada taller, asigna:
1. Un puntaje de compatibilidad (match_score) del 0 al 100 considerando:
   - Especialidades del taller vs tipo de problema (40%)
   - Distancia al cliente (30%)
   - Calificación y reputación (20%)
   - Disponibilidad actual (10%)
   - Para urgencias EMERGENCIA: prioriza distancia y disponibilidad inmediata
   - Para urgencias HIGH: balancea especialidad y proximidad
   - Para urgencias NORMAL: prioriza especialidad y calificación
2. Una breve justificación en español (ai_reasoning, máximo 2 oraciones) de por qué se recomienda.

Responde ÚNICAMENTE con un JSON válido con este formato exacto, sin texto adicional:
{{
  "rankings": [
    {{
      "id": "workshop_id",
      "match_score": 92,
      "ai_reasoning": "Especializado en motor y transmisión con excelente reputación. Ubicado a solo 1.2km y disponible de inmediato."
    }}
  ]
}}

Ordena el array de mayor a menor match_score."""

    # ── Parsing ────────────────────────────────────────────────────────────────

    def _parse_response(
        self, llm_text: str, payload: RankingRequest
    ) -> list[WorkshopRankingItem]:
        workshops_by_id = {w.id: w for w in payload.workshops}

        try:
            clean = llm_text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean)
            rankings = parsed["rankings"]
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("No se pudo parsear la respuesta del LLM: %s", exc)
            # Fallback: devolver todos con score 50
            return [
                WorkshopRankingItem(
                    **w.model_dump(),
                    match_score=50,
                    ai_reasoning="Taller disponible en tu zona.",
                )
                for w in payload.workshops
            ]

        result: list[WorkshopRankingItem] = []
        for rank_item in rankings:
            workshop_id = rank_item.get("id", "")
            original = workshops_by_id.get(workshop_id)
            if original is None:
                continue

            result.append(
                WorkshopRankingItem(
                    **original.model_dump(),
                    match_score=rank_item.get("match_score", 50),
                    ai_reasoning=rank_item.get("ai_reasoning", ""),
                )
            )

        return result
