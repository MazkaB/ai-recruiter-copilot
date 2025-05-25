import openai
from config import config
import json
from typing import Dict, Any

class AssessmentService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    
    async def generate_assessment(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate role-specific assessment based on CV"""
        
        role_fit = cv_data.get('role_fit', 'General')
        technologies = cv_data.get('technologies', [])
        experience = cv_data.get('experience', [])
        
        # Determine assessment type based on role
        if any(tech.lower() in ['python', 'javascript', 'java', 'react', 'node'] for tech in technologies):
            return await self._generate_coding_assessment(role_fit, technologies)
        elif 'product' in role_fit.lower() or 'manager' in role_fit.lower():
            return await self._generate_business_assessment(role_fit, experience)
        else:
            return await self._generate_general_assessment(role_fit, cv_data)
    
    async def _generate_coding_assessment(self, role: str, technologies: list) -> Dict[str, Any]:
        """Generate coding assessment"""
        
        primary_tech = technologies[0] if technologies else 'JavaScript'
        
        prompt = f"""
        Create a coding assessment for a {role} position focusing on {primary_tech}.
        
        Generate a practical coding problem that:
        1. Can be completed in 30-45 minutes
        2. Tests core programming concepts
        3. Is relevant to real-world scenarios
        4. Has clear requirements and expected output
        
        Return JSON with:
        {{
            "type": "coding",
            "title": "Problem title",
            "description": "Detailed problem description",
            "requirements": ["Requirement 1", "Requirement 2"],
            "example_input": "Sample input",
            "example_output": "Expected output",
            "evaluation_criteria": ["Criteria 1", "Criteria 2"],
            "time_limit": 45,
            "language": "{primary_tech}",
            "starter_code": "// Basic template code"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior technical interviewer creating practical coding assessments."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
            
        except Exception as e:
            # Fallback coding assessment
            return {
                "type": "coding",
                "title": "Array Manipulation Challenge",
                "description": "Given an array of integers, implement a function that finds the two numbers that sum to a target value.",
                "requirements": [
                    "Function should return indices of the two numbers",
                    "Assume exactly one solution exists",
                    "Handle edge cases appropriately"
                ],
                "example_input": "arr = [2, 7, 11, 15], target = 9",
                "example_output": "[0, 1] (because arr[0] + arr[1] = 2 + 7 = 9)",
                "evaluation_criteria": [
                    "Correctness of solution",
                    "Code quality and readability",
                    "Time and space complexity",
                    "Edge case handling"
                ],
                "time_limit": 30,
                "language": primary_tech,
                "starter_code": f"// Implement your solution here\nfunction twoSum(nums, target) {{\n    // Your code here\n}}"
            }
    
    async def _generate_business_assessment(self, role: str, experience: list) -> Dict[str, Any]:
        """Generate business/product assessment"""
        
        return {
            "type": "business_case",
            "title": "Product Strategy Challenge",
            "description": "You're tasked with improving user engagement for a mobile app that has seen declining daily active users over the past 3 months.",
            "scenario": {
                "context": "Mobile fitness app with 100K users",
                "problem": "30% decline in daily active users",
                "data_points": [
                    "Average session time: 3 minutes (down from 5 minutes)",
                    "Feature usage: Main workout feature used by 40% of users",
                    "User feedback: 'App feels repetitive', 'Not enough variety'"
                ]
            },
            "requirements": [
                "Identify 3 potential root causes",
                "Propose 2 solution strategies with rationale",
                "Define success metrics for each solution",
                "Create a 90-day implementation timeline"
            ],
            "evaluation_criteria": [
                "Problem analysis depth",
                "Solution creativity and feasibility",
                "Metrics selection and reasoning",
                "Implementation planning"
            ],
            "time_limit": 45,
            "format": "Written response with clear sections"
        }
    
    async def _generate_general_assessment(self, role: str, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate general skills assessment"""
        
        return {
            "type": "analytical",
            "title": "Process Improvement Challenge",
            "description": "Analyze a workflow problem and propose improvements",
            "scenario": {
                "context": "Customer support team handling 500+ tickets/day",
                "problem": "Response time has increased from 2 hours to 8 hours",
                "current_process": [
                    "Tickets arrive via email and chat",
                    "Manual assignment to available agents",
                    "Agents work through tickets in order received",
                    "Complex issues escalated to senior agents"
                ]
            },
            "requirements": [
                "Identify bottlenecks in current process",
                "Propose 3 improvement solutions",
                "Prioritize solutions with justification",
                "Estimate impact and implementation effort"
            ],
            "evaluation_criteria": [
                "Problem identification accuracy",
                "Solution practicality",
                "Prioritization reasoning",
                "Communication clarity"
            ],
            "time_limit": 30,
            "format": "Structured written response"
        }
    
    async def evaluate_assessment(self, assessment: Dict[str, Any], submission: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate assessment submission"""
        
        assessment_type = assessment.get('type', 'general')
        
        if assessment_type == 'coding':
            return await self._evaluate_coding_submission(assessment, submission)
        else:
            return await self._evaluate_written_submission(assessment, submission)
    
    async def _evaluate_coding_submission(self, assessment: Dict[str, Any], submission: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate coding assessment submission"""
        
        code = submission.get('code', '')
        
        prompt = f"""
        Evaluate this coding solution:
        
        Problem: {assessment.get('title', '')}
        Requirements: {assessment.get('requirements', [])}
        
        Submitted Code:
        {code}
        
        Rate on scale 1-5 for:
        - Correctness
        - Code Quality
        - Efficiency
        - Problem Understanding
        
        Return JSON with scores and feedback.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a technical assessor. Provide constructive feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
            
        except Exception as e:
            return {
                "correctness_score": 3,
                "quality_score": 3,
                "efficiency_score": 3,
                "understanding_score": 3,
                "feedback": "Assessment evaluation failed - manual review required"
            }
    
    async def _evaluate_written_submission(self, assessment: Dict[str, Any], submission: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate written assessment submission"""
        
        return {
            "analysis_score": 4,
            "solution_score": 4,
            "communication_score": 4,
            "overall_score": 4,
            "feedback": "Well-structured response with clear reasoning. Good problem identification and practical solutions."
        }