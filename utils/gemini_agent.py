import google.generativeai as genai
import os

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class GeminiAgent:
    def __init__(self, model="gemini-1.5-flash"):
        self.model = genai.GenerativeModel(model)

    def generate(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"⚠️ Gemini API error: {e}"
