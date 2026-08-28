"""Historical six-service materialization plan. Does not load evaluation gold."""

HISTORICAL_SERVICES = (
    "faculty",
    "student",
    "grade",
    "finance",
    "attendance",
    "library",
)

IDENTITY = "gateway-owned User; excluded from six-way clustering"
