import httpx


class LocationProvider:
    """
    Reverse-geocodes latitude/longitude into a human-readable
    location name using OpenStreetMap Nominatim.
    """

    BASE_URL = "https://nominatim.openstreetmap.org/reverse"

    async def get_location_name(
        self,
        latitude: float,
        longitude: float,
    ) -> str:

        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "jsonv2",
            "zoom": 10,
            "addressdetails": 1,
        }

        headers = {
            "User-Agent": "FarmMateAI/1.0",
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                    headers=headers,
                )

                response.raise_for_status()

                data = response.json()

        except httpx.HTTPError:
            return "Current Location"

        address = data.get("address", {})

        # ------------------------------------------------------
        # Prefer the most useful agricultural/local location
        # ------------------------------------------------------

        village = (
            address.get("village")
            or address.get("town")
            or address.get("city")
            or address.get("municipality")
            or address.get("county")
        )

        district = (
            address.get("county")
            or address.get("state_district")
            or address.get("district")
        )

        state = address.get("state")

        # ------------------------------------------------------
        # Build readable location
        # ------------------------------------------------------

        parts: list[str] = []

        if village:
            parts.append(village)

        if district and district != village:
            parts.append(district)

        if state and state not in parts:
            parts.append(state)

        if parts:
            return ", ".join(parts)

        # Nominatim may provide a display_name even when
        # address fields are incomplete.
        display_name = data.get("display_name")

        if display_name:
            return str(display_name).split(",")[0].strip()

        return "Current Location"