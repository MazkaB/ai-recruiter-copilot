import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Voice Settings
    ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice
    
    # Interview Settings
    MAX_QUESTIONS = 8  # Maximum number of questions including follow-ups
    ASSESSMENT_TIME_LIMIT = 45  # minutes
    
    @classmethod
    def validate(cls):
        required = [cls.OPENAI_API_KEY, cls.ELEVENLABS_API_KEY, cls.SUPABASE_URL, cls.SUPABASE_KEY]
        if not all(required):
            raise ValueError("Missing required API keys in environment variables")

config = Config()
config.validate()