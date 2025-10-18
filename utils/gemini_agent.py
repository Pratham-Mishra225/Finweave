import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file.")
genai.configure(api_key=api_key)

def list_available_models():
    """List all available Gemini models and their capabilities"""
    try:
        models = genai.list_models()
        available_models = []
        for model in models:
            model_info = {
                'name': model.name,
                'display_name': getattr(model, 'display_name', 'N/A'),
                'supported_methods': getattr(model, 'supported_generation_methods', [])
            }
            available_models.append(model_info)
        return available_models
    except Exception as e:
        return f"Error listing models: {e}"

def test_gemini_connection():
    """Test the Gemini API connection and list available models"""
    print("Testing Gemini API connection...")
    print(f"API Key configured: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")
    
    models = list_available_models()
    if isinstance(models, str):  # Error occurred
        print(f"❌ Error: {models}")
        return False
    
    print(f"✅ Found {len(models)} available models:")
    for model in models:
        supports_generate = 'generateContent' in model['supported_methods']
        status = "✅" if supports_generate else "❌"
        print(f"  {status} {model['name']} - {model['display_name']}")
    
    return True

class GeminiAgent:
    def __init__(self, model=None):
        # Try to get available models first
        available_models = self.get_available_models()
        
        if model is None:
            # Try common model names in order of preference (with correct naming)
            preferred_models = [
                "models/gemini-2.5-flash",
                "models/gemini-2.0-flash",
                "models/gemini-flash-latest",
                "models/gemini-pro-latest",
                "models/gemini-2.5-pro"
            ]
            
            model_to_use = None
            for preferred in preferred_models:
                if preferred in available_models:
                    model_to_use = preferred
                    break
            
            if not model_to_use and available_models:
                # Use the first available model that supports generateContent
                model_to_use = available_models[0]
            
            if not model_to_use:
                raise Exception("No compatible models found")
                
            model = model_to_use
        
        try:
            self.model = genai.GenerativeModel(model)
            print(f"✅ Using Gemini model: {model}")
        except Exception as e:
            raise Exception(f"Failed to initialize model '{model}': {e}")
    
    def get_available_models(self):
        """Get list of available models that support generateContent"""
        try:
            models = genai.list_models()
            compatible_models = []
            for model in models:
                if hasattr(model, 'supported_generation_methods') and 'generateContent' in model.supported_generation_methods:
                    compatible_models.append(model.name)
            return compatible_models
        except Exception as e:
            print(f"Warning: Could not list models: {e}")
            return []

    def generate(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"⚠️ Gemini API error: {e}"
