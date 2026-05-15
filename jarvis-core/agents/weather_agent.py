import httpx
from services.gemini import general_chat

async def get_weather(entities: dict) -> str:
    try:
        city = entities.get("city", entities.get("location", ""))
        if not city:
            return "Please specify a city for the weather."

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://wttr.in/{city}?format=j1".format(city=city),
                timeout=10
            )
            data = response.json()

        current = data["current_condition"][0]
        temp_c = current["temp_C"]
        feels_like = current["FeelsLikeC"]
        description = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        wind = current["windspeedKmph"]

        # завтра
        tomorrow = data["weather"][1]
        tomorrow_max = tomorrow["maxtempC"]
        tomorrow_min = tomorrow["mintempC"]
        tomorrow_desc = tomorrow["hourly"][4]["weatherDesc"][0]["value"]
        chance_rain = tomorrow["hourly"][4].get("chanceofrain", "0")

        weather_info = f"""City: {city}
Now: {temp_c}°C, feels like {feels_like}°C, {description}
Humidity: {humidity}%, Wind: {wind} km/h
Tomorrow: {tomorrow_min}°C - {tomorrow_max}°C, {tomorrow_desc}, {chance_rain}% chance of rain"""

        summary = await general_chat(
            f"Give a brief JARVIS-style weather report and practical advice. Data:\n{weather_info}"
        )
        return summary

    except Exception as e:
        return f"JARVIS couldn't fetch weather: {str(e)}"
