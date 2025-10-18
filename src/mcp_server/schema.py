from typing import Optional

from pydantic import BaseModel, Field


class GoogleMapsPlacesInput(BaseModel):
    query: str = Field(description="The query to search for restaurants on Google Maps")
    location: Optional[str] = Field(
        description="The location to search for restaurants on Google Maps",
        default=None,
    )
    radius_meters: Optional[int] = Field(
        description="The radius in meters to search for restaurants on Google Maps",
        default=2000,
    )


class GoogleMapsPlacesOutput(BaseModel):
    name: str = Field(description="The name of the restaurant")
    rating: Optional[float] = Field(
        default=None, description="The rating of the restaurant"
    )
    reviews_count: Optional[int] = Field(
        default=None, description="The number of reviews of the restaurant"
    )
    price_level: Optional[int] = Field(
        default=None, description="The price level of the restaurant"
    )
    types: list[str] = Field(
        default_factory=list, description="The types of the restaurant"
    )
    photo_reference: Optional[str] = Field(
        default=None, description="The photo reference of the restaurant"
    )
    place_url: Optional[str] = Field(
        default=None, description="The place url of the restaurant"
    )
