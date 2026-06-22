import math

import pandas as pd
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.store import StoreSearchRequest, StoreSearchResponse, StoreResponse


class StoreRecommendationService:
    def __init__(self):
        self.stores_file = settings.STORES_DATA_PATH

    def find_nearby_stores(self, request: StoreSearchRequest) -> StoreSearchResponse:
        df = self._load_stores_dataset()

        if df.empty:
            return StoreSearchResponse(total=0, stores=[])

        df["distance_km"] = df.apply(
            lambda row: self._haversine_distance(
                request.latitude,
                request.longitude,
                float(row["latitude"]),
                float(row["longitude"])
            ),
            axis=1
        )

        df = df[df["distance_km"] <= request.max_distance_km]

        if request.product_type:
            product_type = request.product_type.lower().strip()

            df = df[
                df["available_products"]
                .astype(str)
                .str.lower()
                .str.contains(product_type, na=False)
            ]

        df = df.sort_values("distance_km")

        stores = [self._row_to_store(row) for _, row in df.iterrows()]

        return StoreSearchResponse(
            total=len(stores),
            stores=stores
        )

    def get_all_stores(self) -> list[StoreResponse]:
        df = self._load_stores_dataset()

        if df.empty:
            return []

        return [self._row_to_store(row) for _, row in df.iterrows()]

    def get_store_by_id(self, store_id: int) -> StoreResponse:
        df = self._load_stores_dataset()

        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucun magasin trouvé."
            )

        result = df[df["id"] == store_id]

        if result.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Magasin introuvable."
            )

        return self._row_to_store(result.iloc[0])

    def _load_stores_dataset(self) -> pd.DataFrame:
        if not self.stores_file.exists():
            return pd.DataFrame()

        try:
            return pd.read_csv(self.stores_file)
        except Exception:
            return pd.DataFrame()

    def _row_to_store(self, row) -> StoreResponse:
        products = row.get("available_products", "")

        if isinstance(products, str):
            available_products = [
                item.strip()
                for item in products.split("|")
                if item.strip()
            ]
        else:
            available_products = []

        return StoreResponse(
            id=int(row.get("id", 0)),
            name=str(row.get("name", "")),
            store_type=str(row.get("store_type", "physical")),
            city=str(row.get("city", "")),
            address=str(row.get("address", "")),
            latitude=float(row.get("latitude", 0)),
            longitude=float(row.get("longitude", 0)),
            phone=str(row.get("phone", "")),
            website=str(row.get("website", "")),
            available_products=available_products,
            distance_km=round(float(row.get("distance_km", 0)), 2)
            if "distance_km" in row
            else None
        )

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        radius = 6371

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return radius * c