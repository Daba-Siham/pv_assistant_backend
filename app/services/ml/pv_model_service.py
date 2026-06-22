from functools import lru_cache
import math
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.recommendation import PVRecommendationRequest


DEFAULT_OUTPUT_FIELDS = [
    "feasibility",
    "panel_count",
    "panel_power_w",
    "total_panel_power_kwp",
    "battery_needed",
    "battery_capacity_kwh",
    "battery_count",
    "inverter_power_kw",
    "dc_cable_section_mm2",
    "ac_cable_section_mm2",
    "estimated_cost",
    "roi_years",
    "orientation",
    "tilt_angle",
]


class PVModelService:
    def __init__(self, model_path: Path | None = None):
        self.model_path = Path(model_path or settings.PV_RECOMMENDATION_MODEL_PATH)

    def predict(self, request: PVRecommendationRequest) -> dict[str, Any]:
        model = self._load_model(str(self.model_path))
        features = self.prepare_features(request)

        try:
            if self._is_bundle_model(model):
                return self._predict_bundle(model, request)

            raw_prediction = model.predict(features)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur pendant la prediction ML: {exc}",
            ) from exc

        return self._normalize_prediction(raw_prediction)

    def prepare_features(self, request: PVRecommendationRequest) -> pd.DataFrame:
        daily_consumption = request.normalized_daily_consumption_kwh
        shade_factor = request.shade_factor

        if shade_factor is None:
            shade_factor = self._shade_factor_from_label(request.shading)

        monthly_consumption = request.monthly_consumption_kwh or round(daily_consumption * 30, 3)

        return pd.DataFrame(
            [
                {
                    "city": request.city,
                    "daily_consumption_kwh": daily_consumption,
                    "monthly_consumption_kwh": monthly_consumption,
                    "annual_consumption_kwh": round(monthly_consumption * 12, 3),
                    "installation_type": request.installation_type.value,
                    "available_area_m2": request.available_area_m2,
                    "available_roof_area_m2": request.available_area_m2,
                    "budget": request.budget,
                    "budget_dh": request.budget,
                    "autonomy_days": request.autonomy_days,
                    "battery_autonomy_days": request.autonomy_days,
                    "roof_type": request.roof_type,
                    "orientation": request.orientation,
                    "roof_orientation": request.orientation,
                    "tilt_angle": request.tilt_angle,
                    "roof_tilt_deg": request.tilt_angle,
                    "shading": request.shading,
                    "shade_level": self._shade_level_from_label(request.shading),
                    "shade_factor": shade_factor,
                    "distance_panels_inverter_m": request.distance_panels_inverter_m,
                    "distance_panels_to_inverter_m": request.distance_panels_inverter_m,
                    "distance_inverter_house_m": request.distance_inverter_house_m,
                    "distance_inverter_to_load_m": request.distance_inverter_house_m,
                    "electrical_phase": request.electrical_phase.value,
                    "grid_phase": self._grid_phase_value(request.electrical_phase.value),
                    "electricity_tariff": request.electricity_tariff,
                    "electricity_tariff_dh_kwh": request.electricity_tariff,
                    "usable_roof_area_m2": request.available_area_m2,
                    "usable_area_factor": 1.0,
                    "orientation_factor": self._orientation_factor(request.orientation),
                }
            ]
        )

    @staticmethod
    def _shade_factor_from_label(shading: str | None) -> float:
        if not shading:
            return 1.0

        normalized = shading.strip().lower()
        if normalized in {"aucun", "faible", "low", "none"}:
            return 1.0
        if normalized in {"moyen", "medium", "partiel"}:
            return 0.85
        if normalized in {"fort", "high", "important"}:
            return 0.7
        return 1.0

    @staticmethod
    def _shade_level_from_label(shading: str | None) -> str:
        if not shading:
            return "none"

        normalized = shading.strip().lower()
        if normalized in {"aucun", "faible", "low", "none"}:
            return "none"
        if normalized in {"moyen", "medium", "partiel"}:
            return "medium"
        if normalized in {"fort", "high", "important"}:
            return "high"
        return normalized

    @staticmethod
    def _grid_phase_value(phase: str) -> str:
        return "Triphase" if phase == "three_phase" else "Monophase"

    @staticmethod
    def _orientation_factor(orientation: str) -> float:
        normalized = orientation.strip().lower()
        if normalized == "sud":
            return 1.0
        if normalized in {"est", "ouest"}:
            return 0.85
        if normalized == "nord":
            return 0.6
        return 0.9

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_model(model_path: str):
        path = Path(model_path)
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Modele ML introuvable. Place le fichier joblib dans "
                    f"{path} ou configure PV_RECOMMENDATION_MODEL_PATH."
                ),
            )

        model = joblib.load(path)
        PVModelService._force_single_thread(model)
        return model

    @staticmethod
    def _force_single_thread(obj: Any) -> None:
        if isinstance(obj, dict):
            for value in obj.values():
                PVModelService._force_single_thread(value)
            return

        if hasattr(obj, "set_params"):
            try:
                params = obj.get_params(deep=True)
                n_jobs_params = {
                    key: 1 for key in params if key.endswith("n_jobs") or key == "n_jobs"
                }
                if n_jobs_params:
                    obj.set_params(**n_jobs_params)
            except Exception:
                return

    @staticmethod
    def _is_bundle_model(model: Any) -> bool:
        required_keys = {
            "input_features",
            "default_input",
            "feasibility_models",
            "recommendation_categorical_models",
            "recommendation_numeric_model",
        }
        return isinstance(model, dict) and required_keys.issubset(model.keys())

    def _predict_bundle(
        self,
        bundle: dict[str, Any],
        request: PVRecommendationRequest,
    ) -> dict[str, Any]:
        model_input = dict(bundle["default_input"])
        prepared = self.prepare_features(request).iloc[0].to_dict()
        model_input.update({key: value for key, value in prepared.items() if value is not None})

        input_features = bundle["input_features"]
        features = pd.DataFrame([model_input], columns=input_features)

        result: dict[str, Any] = {}

        for target, model_info in bundle.get("feasibility_models", {}).items():
            result[target] = self._predict_one(
                model_info,
                features,
                bundle.get("feasibility_encoders", {}).get(target),
            )

        for target, model_info in bundle.get("recommendation_categorical_models", {}).items():
            result[target] = self._predict_one(
                model_info,
                features,
                bundle.get("recommendation_categorical_encoders", {}).get(target),
            )

        numeric_prediction = bundle["recommendation_numeric_model"].predict(features)[0]
        for target, value in zip(bundle.get("numeric_recommendation_targets", []), numeric_prediction):
            result[target] = self._clean_value(value)

        self._normalize_numeric_recommendations(result)
        self._add_normalized_aliases(result)
        return result

    def _predict_one(self, model_info: Any, features: pd.DataFrame, encoder: Any = None) -> Any:
        pipeline = model_info.get("pipeline") if isinstance(model_info, dict) else model_info
        value = pipeline.predict(features)[0]

        if encoder is not None:
            try:
                value = encoder.inverse_transform([value])[0]
            except Exception:
                pass

        return self._clean_value(value)

    @staticmethod
    def _add_normalized_aliases(result: dict[str, Any]) -> None:
        aliases = {
            "battery_required": "battery_needed",
            "battery_units": "battery_count",
            "inverter_rated_power_kw": "inverter_power_kw",
            "estimated_total_cost_dh": "estimated_cost",
            "recommended_orientation": "orientation",
            "recommended_tilt_deg": "tilt_angle",
        }

        for source, target in aliases.items():
            if source in result and target not in result:
                result[target] = result[source]

        panel_count = PVModelService._as_float(result.get("panel_count"))
        panel_power_w = PVModelService._as_float(result.get("panel_power_w"))
        if panel_count is not None and panel_power_w is not None:
            result["total_panel_power_kwp"] = round(panel_count * panel_power_w / 1000, 3)

    @staticmethod
    def _normalize_numeric_recommendations(result: dict[str, Any]) -> None:
        ceil_fields = {"panel_count", "battery_units"}
        round_fields = {
            "panel_power_w": 0,
            "battery_capacity_kwh": 2,
            "inverter_rated_power_kw": 2,
            "dc_cable_section_mm2": 2,
            "ac_cable_section_mm2": 2,
            "estimated_total_cost_dh": 2,
            "roi_years": 2,
            "recommended_tilt_deg": 0,
        }

        for field in ceil_fields:
            value = PVModelService._as_float(result.get(field))
            if value is not None:
                result[field] = int(math.ceil(max(value, 0)))

        for field, decimals in round_fields.items():
            value = PVModelService._as_float(result.get(field))
            if value is not None:
                result[field] = round(value, decimals)

    @staticmethod
    def _clean_value(value: Any) -> Any:
        if hasattr(value, "item"):
            return value.item()
        if isinstance(value, float) and np.isnan(value):
            return None
        return value

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _normalize_prediction(self, raw_prediction: Any) -> dict[str, Any]:
        if isinstance(raw_prediction, pd.DataFrame):
            return raw_prediction.iloc[0].replace({np.nan: None}).to_dict()

        if isinstance(raw_prediction, pd.Series):
            return raw_prediction.replace({np.nan: None}).to_dict()

        if isinstance(raw_prediction, list) and raw_prediction:
            first = raw_prediction[0]
            if isinstance(first, dict):
                return first
            return self._array_to_dict(first)

        if isinstance(raw_prediction, np.ndarray):
            if raw_prediction.dtype == object and raw_prediction.size and isinstance(raw_prediction.flat[0], dict):
                return raw_prediction.flat[0]
            first = raw_prediction[0] if raw_prediction.ndim > 1 else raw_prediction
            return self._array_to_dict(first)

        if isinstance(raw_prediction, dict):
            return raw_prediction

        return {"prediction": raw_prediction}

    @staticmethod
    def _array_to_dict(values: Any) -> dict[str, Any]:
        array = np.asarray(values).flatten().tolist()
        return {
            field: value.item() if hasattr(value, "item") else value
            for field, value in zip(DEFAULT_OUTPUT_FIELDS, array)
        }
