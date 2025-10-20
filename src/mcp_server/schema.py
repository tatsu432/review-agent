from typing import Any, Dict, Optional

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


class YelpReviewInput(BaseModel):
    restaurant_name: str = Field(
        description="The name of the restaurant to search for on Yelp"
    )
    location: Optional[str] = Field(
        description="The location to search for the restaurant on Yelp",
        default=None,
    )


class YelpReview(BaseModel):
    text: str = Field(description="The review text")
    rating: int = Field(description="The rating given by the reviewer (1-5)")
    user_name: str = Field(description="The name of the reviewer")
    time_created: str = Field(description="When the review was created")
    url: Optional[str] = Field(default=None, description="URL to the review on Yelp")


class YelpBusinessOutput(BaseModel):
    name: str = Field(description="The name of the restaurant")
    yelp_rating: Optional[float] = Field(
        default=None, description="The Yelp rating of the restaurant"
    )
    yelp_review_count: Optional[int] = Field(
        default=None, description="The number of Yelp reviews"
    )
    yelp_url: Optional[str] = Field(
        default=None, description="The Yelp URL of the restaurant"
    )
    reviews: list[YelpReview] = Field(
        default_factory=list,
        description="Note: Individual reviews are not available through Yelp API",
    )


class TaberoguSearchInput(BaseModel):
    query: str = Field(description="The query to search for restaurants on Taberogu")
    ward: Optional[str] = Field(
        description="The ward to search for restaurants on Taberogu",
        default=None,
    )
    max_dinner_budget: Optional[int] = Field(
        description="The maximum dinner budget to search for restaurants on Taberogu",
        default=None,
    )
    smoking: Optional[str] = Field(
        description="The smoking policy to search for restaurants on Taberogu",
        default=None,
    )
    with_children: Optional[bool] = Field(
        description="Whether to search for restaurants that allow children on Taberogu",
        default=None,
    )
    category_hint: Optional[str] = Field(
        description="The category hint to search for restaurants on Taberogu",
        default=None,
    )
    k: int = Field(description="The number of restaurants to return", default=10)


class TaberoguSearchOutput(BaseModel):
    status: str = Field(description="The status of the search")
    results: list[Dict[str, Any]] = Field(
        description="The results of the search",
        default_factory=list,
    )
    retryable: bool = Field(
        description="Whether the search can be retried", default=False
    )


class TaberoguNameLookupInput(BaseModel):
    name: str = Field(description="Restaurant name to retrieve from Taberogu DB")
    min_score: float = Field(
        description="Minimum semantic similarity (0-1) required to accept the match",
        default=0.75,
        ge=0.0,
        le=1.0,
    )


class TaberoguNameLookupOutput(BaseModel):
    status: str = Field(description="The status of the lookup")
    restaurant: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Restaurant record if match exceeds min_score; otherwise None",
    )
    retryable: bool = Field(
        description="Whether the request can be retried", default=False
    )
