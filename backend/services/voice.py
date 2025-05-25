import openai
import requests
from config import config
import io
from typing import BinaryIO

class VoiceService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.elevenlabs_url = "https://api.elevenlabs.io/v1"
        self.voice_id = config.ELEVENLABS_VOICE_ID
    
    async def speech_to_text(self, audio_content: bytes) -> str:
        """Convert speech to text using OpenAI Whisper"""
        try:
            # Create a file-like object from bytes
            audio_file = io.BytesIO(audio_content)
            audio_file.name = "audio.webm"  # Set a filename for the API
            
            # Use OpenAI Whisper API
            response = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            
            return response
            
        except Exception as e:
            raise Exception(f"Speech to text conversion failed: {str(e)}")
    
    async def text_to_speech(self, text: str) -> BinaryIO:
        """Convert text to speech using ElevenLabs"""
        try:
            url = f"{self.elevenlabs_url}/text-to-speech/{self.voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": config.ELEVENLABS_API_KEY
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            # Run the synchronous request in a thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            
            def make_request():
                response = requests.post(url, json=data, headers=headers, timeout=30)
                if response.status_code == 200:
                    return response.content
                else:
                    raise Exception(f"ElevenLabs API error: {response.status_code} - {response.text}")
            
            content = await loop.run_in_executor(None, make_request)
            return io.BytesIO(content)
                
        except Exception as e:
            # Log the error for debugging
            print(f"Text to speech error: {str(e)}")
            
            # For MVP, disable TTS if it fails and return None
            # Frontend will handle gracefully
            return None
    
    def get_supported_audio_formats(self) -> list:
        """Return list of supported audio formats"""
        return ["webm", "mp3", "wav", "m4a", "ogg"]
    
    async def validate_audio_format(self, audio_content: bytes, filename: str) -> bool:
        """Validate if audio format is supported"""
        try:
            # Basic validation - check file extension
            supported_extensions = ['.webm', '.mp3', '.wav', '.m4a', '.ogg']
            file_extension = filename.lower().split('.')[-1]
            
            return f".{file_extension}" in supported_extensions
            
        except Exception:
            return False