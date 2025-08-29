import os
import streamlit as st
from groq import Groq

class AIAgent:
    def __init__(self):
        api_key = st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in secrets.toml or environment.")
        self.client = Groq(api_key=api_key)

    def generate_response(self, prompt):
        result = ""
        completion = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_completion_tokens=8192,
            top_p=1,
            reasoning_effort="medium",
            stream=True,
            stop=None
        )
        for chunk in completion:
            delta = chunk.choices[0].get('delta') if hasattr(chunk.choices[0], 'get') else getattr(chunk.choices[0], 'delta', None)
            if delta:
                content = delta.get('content') if hasattr(delta, 'get') else getattr(delta, 'content', None)
                if content:
                    result += content
        return result
