import openai
from config import config
import json
import PyPDF2
import io
from typing import Dict, Any

class CVParser:
    def __init__(self):
        openai.api_key = config.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    
    async def parse_cv(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Parse CV and extract structured information"""
        
        # Extract text from PDF
        text_content = self._extract_text_from_pdf(file_content, filename)
        
        # Use OpenAI to analyze CV
        analysis_prompt = f"""
        Analyze this CV/Resume and extract structured information. Return a JSON object with the following structure:
        
        {{
            "candidate_name": "Full name",
            "email": "email@example.com",
            "phone": "phone number",
            "summary": "Brief professional summary (2-3 sentences)",
            "experience": [
                {{
                    "company": "Company name",
                    "role": "Job title",
                    "duration": "Start - End dates",
                    "description": "Key responsibilities and achievements"
                }}
            ],
            "skills": ["skill1", "skill2", "skill3"],
            "education": [
                {{
                    "institution": "School/University",
                    "degree": "Degree type",
                    "field": "Field of study",
                    "year": "Graduation year"
                }}
            ],
            "technologies": ["tech1", "tech2", "tech3"],
            "role_fit": "Suggested role type based on experience (e.g., 'Senior Frontend Developer', 'Product Manager', etc.)"
        }}
        
        CV Content:
        {text_content}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert CV analyzer. Extract information accurately and return valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            
            # Clean the result - sometimes GPT returns markdown code blocks
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            elif result.startswith("```"):
                result = result.replace("```", "").strip()
            
            # Parse JSON response
            cv_data = json.loads(result)
            
            # Add metadata
            cv_data["original_filename"] = filename
            cv_data["raw_text"] = text_content[:1000]  # First 1000 chars for reference
            
            return cv_data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in CV analysis: {str(e)}")
            print(f"Raw response: {result[:500]}...")
            # Fallback basic parsing
            return self._create_fallback_cv_data(text_content, filename, str(e))
        except Exception as e:
            print(f"CV analysis error: {str(e)}")
            return self._create_fallback_cv_data(text_content, filename, str(e))
    
    def _extract_text_from_pdf(self, file_content: bytes, filename: str) -> str:
        """Extract text from PDF file"""
        try:
            if filename.lower().endswith('.pdf'):
                pdf_file = io.BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text
            else:
                # Assume it's a text file
                return file_content.decode('utf-8')
                
        except Exception as e:
            return f"Failed to extract text: {str(e)}"
    
    def _extract_email(self, text: str) -> str:
        """Basic email extraction fallback"""
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else "unknown@example.com"
    
    def _create_fallback_cv_data(self, text_content: str, filename: str, error: str) -> dict:
        """Create fallback CV data when parsing fails"""
        return {
            "candidate_name": "Unknown",
            "email": self._extract_email(text_content),
            "summary": "CV analysis failed - manual review required",
            "experience": [],
            "skills": [],
            "education": [],
            "technologies": [],
            "role_fit": "General",
            "raw_text": text_content[:1000],
            "original_filename": filename,
            "error": f"CV parsing failed: {error}"
        }