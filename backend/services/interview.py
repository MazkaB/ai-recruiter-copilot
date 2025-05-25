import openai
from config import config
import json
from typing import List, Dict, Any

class InterviewService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    
    async def generate_questions(self, cv_data: Dict[str, Any]) -> List[str]:
        """Generate tailored interview questions based on CV"""
        
        prompt = f"""
        Based on this candidate's CV, generate 6-8 interview questions that cover:
        1. Behavioral questions (2-3)
        2. Technical questions based on their experience (2-3)
        3. Situational questions relevant to their role (2-3)
        
        Candidate Profile:
        - Name: {cv_data.get('candidate_name', 'Unknown')}
        - Role Fit: {cv_data.get('role_fit', 'General')}
        - Experience: {json.dumps(cv_data.get('experience', []))}
        - Skills: {cv_data.get('skills', [])}
        - Technologies: {cv_data.get('technologies', [])}
        
        Return a JSON array of questions. Each question should be conversational and suitable for voice interview.
        Focus on questions that will help assess the candidate's fit for the role and reveal their problem-solving approach.
        
        Example format:
        [
            "Tell me about a challenging project you worked on recently and how you overcame the obstacles.",
            "How would you approach debugging a performance issue in a React application?",
            "Describe a time when you had to work with a difficult team member. How did you handle it?"
        ]
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert technical recruiter. Generate thoughtful, relevant interview questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            result = response.choices[0].message.content
            
            # Clean the result - sometimes GPT returns markdown code blocks
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            elif result.startswith("```"):
                result = result.replace("```", "").strip()
            
            questions = json.loads(result)
            
            # Add opening and closing questions
            opening = "Hi! Thanks for joining this interview session. Let's start with you telling me a bit about yourself and your current role."
            closing = "That covers the main questions I had. Do you have any questions about the role, company, or anything else you'd like to discuss?"
            
            return [opening] + questions + [closing]
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in question generation: {str(e)}")
            return self._get_fallback_questions()
        except Exception as e:
            print(f"Question generation error: {str(e)}")
            return self._get_fallback_questions()
    
    def _get_fallback_questions(self) -> List[str]:
        """Get fallback generic questions when AI generation fails"""
        return [
            "Hi! Thanks for joining this interview session. Tell me about yourself and your background.",
            "What interests you most about this opportunity?",
            "Describe a challenging project you've worked on recently.",
            "How do you approach problem-solving in your work?",
            "Tell me about a time you had to learn something new quickly.",
            "How do you handle working under pressure or tight deadlines?",
            "What are your career goals for the next few years?",
            "Do you have any questions for me about the role or company?"
        ]
    
    async def generate_followup(self, answer_data: Dict[str, Any]) -> str:
        """Generate follow-up question based on candidate's answer"""
        
        question = answer_data.get('question', '')
        answer = answer_data.get('answer', '')
        
        # Only generate follow-up for very short answers (less than 15 words)
        # and avoid generating follow-ups for follow-up questions
        if (len(answer.split()) >= 15 or 
            "elaborate" in question.lower() or 
            "specific example" in question.lower() or
            "could you provide" in question.lower()):
            return None
        
        # Simple follow-up prompts based on question type
        if "project" in question.lower():
            return "Could you elaborate on the specific challenges you faced in that project?"
        elif "team" in question.lower() or "work" in question.lower():
            return "Can you give me a specific example of how you handled that situation?"
        elif "experience" in question.lower():
            return "What was the outcome of that experience?"
        else:
            return "Could you provide more details about that?"
        
        return None  # No follow-up needed
    
    async def evaluate_answer(self, question: str, answer: str, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate answer quality for reporting"""
        
        prompt = f"""
        Evaluate this interview answer based on the MERIT AI rubric:
        
        Question: {question}
        Answer: {answer}
        
        Candidate Background: {cv_data.get('summary', '')}
        
        Rate the answer on a scale of 1-5 for:
        1. Communication & Clarity
        2. Technical Knowledge (if applicable)
        3. Problem Solving Approach
        4. Professionalism
        5. Cultural Fit Indicators
        
        Return JSON with scores and brief explanations:
        {{
            "communication_score": 4,
            "technical_score": 3,
            "problem_solving_score": 4,
            "professionalism_score": 5,
            "culture_fit_score": 4,
            "overall_notes": "Clear communication, good examples, shows initiative"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert interviewer using the MERIT AI evaluation rubric. Be fair but thorough in your assessment."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
            
        except Exception as e:
            return {
                "communication_score": 3,
                "technical_score": 3,
                "problem_solving_score": 3,
                "professionalism_score": 3,
                "culture_fit_score": 3,
                "overall_notes": f"Auto-evaluation failed: {str(e)}"
            }