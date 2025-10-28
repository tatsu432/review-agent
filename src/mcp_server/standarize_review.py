from __future__ import annotations

from fastmcp import FastMCP

standarize_review_mcp = FastMCP("standarize_review_mcp")


@standarize_review_mcp.tool(
    name="compute_standarized_review_score",
    description=(
        "Compute a single review metric from Google, Tabelog, and Yelp by "
        "taking a weighted sum of standardized scores (z-scores), where "
        "weights are proportional to review counts. The final score is then "
        "mapped back to a 1-5 scale via 3.5 + 0.5 * z_avg."
    ),
)
def compute_standarized_review_score(
    google_review_score: float | None = None,
    google_review_count: int | None = None,
    taberogu_review_score: float | None = None,
    taberogu_review_count: int | None = None,
    yelp_review_score: float | None = None,
    yelp_review_count: int | None = None,
) -> float | None:
    """
    Returns a single mapped score in [approximately] 1-5, or None if no counts provided.
    """

    mu = {"google": 3.8, "tabelog": 3.1, "yelp": 4.0}
    sigma = {"google": 0.4, "tabelog": 0.35, "yelp": 0.5}

    # Collect counts and compute total
    counts: dict[str, int] = {
        "google": int(google_review_count) if google_review_count else 0,
        "tabelog": int(taberogu_review_count) if taberogu_review_count else 0,
        "yelp": int(yelp_review_count) if yelp_review_count else 0,
    }
    total_count = sum(counts.values())
    if total_count == 0:
        return None

    # Compute z-scores where available
    def z(score: float | None, source: str) -> float | None:
        if score is None:
            return None
        return (float(score) - mu[source]) / sigma[source]

    z_google = z(google_review_score, "google")
    z_tabelog = z(taberogu_review_score, "tabelog")
    z_yelp = z(yelp_review_score, "yelp")

    # Weights proportional to counts; missing scores get zero weight effectively
    weighted_sum = 0.0
    for source, z_val in (
        ("google", z_google),
        ("tabelog", z_tabelog),
        ("yelp", z_yelp),
    ):
        if z_val is None or counts[source] == 0:
            continue
        weight = counts[source] / total_count
        weighted_sum += weight * z_val

    # Map back to 1-5 scale
    mapped_score = 3.5 + 0.5 * weighted_sum
    return float(mapped_score)
