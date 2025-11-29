"""Gemini AI configuration and client initialization."""
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Global model instance
_gemini_model = None
_gemini_vision_model = None


def initialize_gemini():
    """Initialize Gemini AI with API key from settings."""
    global _gemini_model, _gemini_vision_model
    
    try:
        genai.configure(api_key=settings.gemini_api_key)  # type: ignore[attr-defined]
        
        # Configure generation parameters for text model
        generation_config = GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=2048,
        )
        
        # Safety settings - allow financial content
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]
        
        # Initialize the text model (gemini-2.0-flash-exp)
        _gemini_model = genai.GenerativeModel(  # type: ignore[attr-defined]
            model_name="gemini-2.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
        
        # Initialize vision model for receipt scanning
        _gemini_vision_model = genai.GenerativeModel(  # type: ignore[attr-defined]
            model_name="gemini-2.0-flash-exp",
            generation_config=GenerationConfig(
                temperature=0.2,  # Lower temperature for OCR tasks
                max_output_tokens=1024,
            ),
            safety_settings=safety_settings,
        )
        
        logger.info("Gemini AI initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Gemini AI: {e}")
        return False


def get_gemini_model():
    """Get the initialized Gemini model for text generation."""
    global _gemini_model
    
    if _gemini_model is None:
        initialize_gemini()
    
    return _gemini_model


def get_gemini_vision_model():
    """Get the initialized Gemini vision model for image analysis."""
    global _gemini_vision_model
    
    if _gemini_vision_model is None:
        initialize_gemini()
    
    return _gemini_vision_model
