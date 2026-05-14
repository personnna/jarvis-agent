import httpx
from services.gemini import general_chat

async def research(entities: dict) -> str:
    try:
        query = entities.get("query", "")
        if not query:
            return "Please specify what to research."

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1
                },
                headers={"User-Agent": "JARVIS/1.0"},
                follow_redirects=True,
                timeout=10
            )
            data = response.json()

        results = []

        # основной ответ
        if data.get("Abstract"):
            results.append(data["Abstract"])

        # related topics
        for topic in data.get("RelatedTopics", [])[:5]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(topic["Text"])

        if not results:
            # fallback — просто спрашиваем LLM
            summary = await general_chat(
                f"As JARVIS, give me 5 practical bullet points about: {query}"
            )
            return f"Research: {query}\n\n{summary}"

        context = "\n".join(results)
        prompt = f"""Summarize this for a developer. Max 5 bullet points. Be direct and practical.

Query: {query}
Info: {context}"""

        summary = await general_chat(prompt)
        return f"Research: {query}\n\n{summary}"

    except Exception as e:
        return f"JARVIS couldn't research: {str(e)}"
