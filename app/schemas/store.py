from pydantic import BaseModel, Field


class StoreSearchRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    max_distance_km: float = Field(default=50, gt=0)
    product_type: str | None = None


class StoreResponse(BaseModel):
    id: int
    name: str
    store_type: str
    city: str
    address: str | None = None
    latitude: float
    longitude: float
    phone: str | None = None
    website: str | None = None
    available_products: list[str] = []
    distance_km: float | None = None


class StoreSearchResponse(BaseModel):
    total: int
    stores: list[StoreResponse]