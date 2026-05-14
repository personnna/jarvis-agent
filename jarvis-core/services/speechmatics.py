import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

async def transcribe_audio(audio_bytes: bytes, language: str = "auto") -> str:
    try:
        api_key = os.getenv("SPEECHMATICS_API_KEY")

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://asr.api.speechmatics.com/v2/jobs/",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"data_file": ("audio.wav", audio_bytes, "audio/wav")},
                data={
                    "config": json.dumps({
                        "type": "transcription",
                        "transcription_config": {
                            "language": language,
                            "operating_point": "enhanced"
                        }
                    })
                }
            )

            if response.status_code != 201:
                return f"Error submitting job: {response.text}"

            job_id = response.json()["id"]
            print(f"[SPEECHMATICS] Job created: {job_id}")

            # ждём результат
            import asyncio
            for _ in range(30):
                await asyncio.sleep(2)
                result = await client.get(
                    f"https://asr.api.speechmatics.com/v2/jobs/{job_id}/transcript",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Accept": "application/json"
                    }
                )
                if result.status_code == 200:
                    data = result.json()
                    words = [
                        w["alternatives"][0]["content"]
                        for w in data.get("results", [])
                        if w.get("alternatives")
                    ]
                    transcript = " ".join(words)
                    print(f"[SPEECHMATICS] Transcript: {transcript}")
                    return transcript

            return "Transcription timed out."

    except Exception as e:
        return f"Speechmatics error: {str(e)}"
