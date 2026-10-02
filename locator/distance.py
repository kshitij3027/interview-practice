from __future__ import annotations

import math

EARTH_RADIUS_METERS = 6_371_008.8


def great_circle_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return spherical great-circle distance in meters for validated coordinates."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)

    sin_dphi = math.sin(dphi / 2.0)
    sin_dlambda = math.sin(dlambda / 2.0)
    a = sin_dphi * sin_dphi + math.cos(phi1) * math.cos(phi2) * sin_dlambda * sin_dlambda
    a = min(1.0, max(0.0, a))
    central_angle = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_METERS * central_angle
