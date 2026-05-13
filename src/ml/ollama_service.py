import requests
import json


class OllamaService:

    def __init__(self, model="qwen2.5:7b"):
        self.model = model
        self.url = "http://ollama:11434/api/generate"

    def generate(self, prompt: str) -> str:
        try:
            response = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )

            print("STATUS:", response.status_code)
            print("TEXT:", response.text)

            data = response.json()
            return data.get("response", "")

        except Exception as e:
            print("OLLAMA ERROR:", e)
            return "AI summary unavailable"