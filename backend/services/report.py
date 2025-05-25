import openai
from config import config
import json
from typing import Dict, Any
from datetime import datetime
from models.session import InterviewSession

class ReportService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    
    async def generate_report(self, session: InterviewSession) -> Dict[str, Any]:
        """Generate comprehensive evaluation report"""
        
        # Gather all session data
        cv_data = session.cv_data or {}
        answers = session.answers or []
        assessment_result = session.assessment_result or {}
        
        # Generate individual section scores
        interview_scores = await self._evaluate_interview_performance(answers, cv_data)
        assessment_scores = self._process_assessment_scores(assessment_result)
        overall_evaluation = self._generate_overall_evaluation(
            cv_data, interview_scores, assessment_scores
        )
        
        # Compile final report
        report = {
            "candidate_info": {
                "name": cv_data.get('candidate_name', 'Unknown'),
                "email": cv_data.get('email', 'Unknown'),
                "role_applied": cv_data.get('role_fit', 'General'),
                "evaluation_date": datetime.now().isoformat()
            },
            "cv_analysis": {
                "summary": cv_data.get('summary', ''),
                "experience_years": self._calculate_experience_years(cv_data.get('experience', [])),
                "key_skills": cv_data.get('skills', [])[:8],  # Top 8 skills
                "technologies": cv_data.get('technologies', [])[:10],  # Top 10 technologies
                "education_level": self._determine_education_level(cv_data.get('education', []))
            },
            "interview_evaluation": {
                "questions_answered": len(answers),
                "scores": interview_scores,
                "strengths": self._identify_strengths(interview_scores),
                "areas_for_improvement": self._identify_improvements(interview_scores),
                "notable_responses": self._extract_notable_responses(answers)
            },
            "assessment_evaluation": {
                "completed": bool(assessment_result),
                "scores": assessment_scores,
                "performance_summary": self._summarize_assessment_performance(assessment_scores)
            },
            "overall_evaluation": overall_evaluation,
            "recommendation": self._generate_recommendation(overall_evaluation),
            "next_steps": self._suggest_next_steps(overall_evaluation),
            "session_metadata": {
                "session_id": session.session_id,
                "duration_minutes": self._calculate_session_duration(session),
                "completion_status": session.status
            }
        }
        
        return report
    
    async def _evaluate_interview_performance(self, answers: list, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate interview responses using MERIT rubric"""
        
        if not answers:
            return self._default_interview_scores()
        
        try:
            # Compile all Q&A for evaluation
            qa_text = "\n\n".join([f"Q: {ans.get('question', '')}\nA: {ans.get('answer', '')}" for ans in answers])
            
            prompt = f"""
            Evaluate this interview performance using the MERIT AI rubric:
            
            Candidate Background: {cv_data.get('summary', '')}
            Role: {cv_data.get('role_fit', 'General')}
            
            Interview Q&A:
            {qa_text}
            
            Rate on scale 1-5 for each MERIT dimension:
            1. Communication & English Proficiency
            2. Technical Knowledge & Role Fit  
            3. Problem Solving & Thinking
            4. Professionalism & Digital Presence
            5. Culture & Work Ethic Alignment
            
            Return JSON with:
            {{
                "communication_score": 4,
                "technical_score": 3,
                "problem_solving_score": 4,
                "professionalism_score": 5,
                "culture_fit_score": 4,
                "overall_interview_score": 4.0,
                "detailed_feedback": {{
                    "communication": "Clear and articulate responses...",
                    "technical": "Good technical knowledge but...",
                    "problem_solving": "Shows structured thinking...",
                    "professionalism": "Professional demeanor throughout...",
                    "culture_fit": "Demonstrates good cultural alignment..."
                }}
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert interviewer using the MERIT AI evaluation rubric. Be thorough and fair."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in interview evaluation: {str(e)}")
            return self._default_interview_scores()
        except Exception as e:
            print(f"Interview evaluation error: {str(e)}")
            return self._default_interview_scores()
    
    def _default_interview_scores(self) -> Dict[str, Any]:
        """Default scores when evaluation fails"""
        return {
            "communication_score": 3,
            "technical_score": 3,
            "problem_solving_score": 3,
            "professionalism_score": 3,
            "culture_fit_score": 3,
            "overall_interview_score": 3.0,
            "detailed_feedback": {
                "communication": "Unable to evaluate - technical error",
                "technical": "Unable to evaluate - technical error",
                "problem_solving": "Unable to evaluate - technical error",
                "professionalism": "Unable to evaluate - technical error",
                "culture_fit": "Unable to evaluate - technical error"
            }
        }
    
    def _process_assessment_scores(self, assessment_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process assessment scores into standardized format"""
        
        if not assessment_result:
            return {"completed": False, "overall_score": 0}
        
        # Extract scores based on assessment type
        if 'correctness_score' in assessment_result:  # Coding assessment
            return {
                "completed": True,
                "correctness": assessment_result.get('correctness_score', 0),
                "quality": assessment_result.get('quality_score', 0),
                "efficiency": assessment_result.get('efficiency_score', 0),
                "overall_score": sum([
                    assessment_result.get('correctness_score', 0),
                    assessment_result.get('quality_score', 0),
                    assessment_result.get('efficiency_score', 0)
                ]) / 3
            }
        else:  # Written assessment
            return {
                "completed": True,
                "analysis": assessment_result.get('analysis_score', 0),
                "solution": assessment_result.get('solution_score', 0),
                "communication": assessment_result.get('communication_score', 0),
                "overall_score": assessment_result.get('overall_score', 0)
            }
    
    def _generate_overall_evaluation(self, cv_data: Dict[str, Any], interview_scores: Dict[str, Any], assessment_scores: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall candidate evaluation"""
        
        # Calculate weighted overall score
        interview_weight = 0.6
        assessment_weight = 0.4
        
        interview_avg = interview_scores.get('overall_interview_score', 3.0)
        assessment_avg = assessment_scores.get('overall_score', 0)
        
        if assessment_scores.get('completed', False):
            overall_score = (interview_avg * interview_weight) + (assessment_avg * assessment_weight)
        else:
            overall_score = interview_avg  # Only interview if no assessment
        
        # Determine recommendation level
        if overall_score >= 4.5:
            recommendation = "Strong Hire"
            confidence = "High"
        elif overall_score >= 3.5:
            recommendation = "Hire"
            confidence = "Medium-High"
        elif overall_score >= 2.5:
            recommendation = "Maybe"
            confidence = "Medium"
        else:
            recommendation = "No Hire"
            confidence = "High"
        
        return {
            "overall_score": round(overall_score, 2),
            "recommendation": recommendation,
            "confidence_level": confidence,
            "score_breakdown": {
                "interview_score": interview_avg,
                "assessment_score": assessment_avg,
                "cv_quality": self._assess_cv_quality(cv_data)
            }
        }
    
    def _generate_recommendation(self, overall_evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hiring recommendation with reasoning"""
        
        score = overall_evaluation.get('overall_score', 3.0)
        recommendation = overall_evaluation.get('recommendation', 'Maybe')
        
        reasoning_map = {
            "Strong Hire": "Exceptional candidate who exceeded expectations across all evaluation criteria. Ready for immediate hiring.",
            "Hire": "Strong candidate who meets role requirements with good potential for growth. Recommended for hire.",
            "Maybe": "Candidate shows promise but has some gaps. Consider for junior role or with additional training.",
            "No Hire": "Candidate does not currently meet the role requirements. Consider for future opportunities after skill development."
        }
        
        return {
            "decision": recommendation,
            "reasoning": reasoning_map.get(recommendation, "Standard evaluation completed."),
            "confidence_score": overall_evaluation.get('confidence_level', 'Medium'),
            "follow_up_required": recommendation == "Maybe"
        }
    
    def _suggest_next_steps(self, overall_evaluation: Dict[str, Any]) -> list:
        """Suggest next steps based on evaluation"""
        
        recommendation = overall_evaluation.get('recommendation', 'Maybe')
        
        next_steps_map = {
            "Strong Hire": [
                "Schedule final interview with hiring manager",
                "Prepare offer package",
                "Check references",
                "Begin onboarding preparation"
            ],
            "Hire": [
                "Schedule follow-up interview with team lead",
                "Verify specific technical skills if needed",
                "Check references",
                "Prepare offer discussion"
            ],
            "Maybe": [
                "Schedule additional technical interview",
                "Consider pairing with senior developer for assessment",
                "Evaluate for alternative roles",
                "Provide feedback and reassess in 3-6 months"
            ],
            "No Hire": [
                "Provide constructive feedback to candidate",
                "Keep profile for future opportunities",
                "Consider referral to other suitable positions",
                "Maintain positive candidate experience"
            ]
        }
        
        return next_steps_map.get(recommendation, ["Manual review required"])
    
    # Helper methods
    def _calculate_experience_years(self, experience: list) -> int:
        """Calculate total years of experience"""
        return len(experience) * 2  # Rough estimate - 2 years per role
    
    def _determine_education_level(self, education: list) -> str:
        """Determine highest education level"""
        if not education:
            return "Not specified"
        
        degrees = [edu.get('degree', '').lower() for edu in education]
        
        if any('phd' in deg or 'doctorate' in deg for deg in degrees):
            return "Doctorate"
        elif any('master' in deg or 'mba' in deg for deg in degrees):
            return "Master's"
        elif any('bachelor' in deg or 'degree' in deg for deg in degrees):
            return "Bachelor's"
        else:
            return "Other"
    
    def _assess_cv_quality(self, cv_data: Dict[str, Any]) -> float:
        """Assess CV quality on 1-5 scale"""
        score = 3.0  # Base score
        
        if cv_data.get('summary'):
            score += 0.3
        if len(cv_data.get('experience', [])) >= 2:
            score += 0.4
        if len(cv_data.get('skills', [])) >= 5:
            score += 0.3
        
        return min(5.0, score)
    
    def _identify_strengths(self, interview_scores: Dict[str, Any]) -> list:
        """Identify candidate strengths from scores"""
        strengths = []
        
        if interview_scores.get('communication_score', 0) >= 4:
            strengths.append("Excellent communication skills")
        if interview_scores.get('technical_score', 0) >= 4:
            strengths.append("Strong technical knowledge")
        if interview_scores.get('problem_solving_score', 0) >= 4:
            strengths.append("Good problem-solving approach")
        if interview_scores.get('culture_fit_score', 0) >= 4:
            strengths.append("Great cultural fit")
        
        return strengths or ["Shows potential in multiple areas"]
    
    def _identify_improvements(self, interview_scores: Dict[str, Any]) -> list:
        """Identify areas for improvement"""
        improvements = []
        
        if interview_scores.get('communication_score', 5) < 3:
            improvements.append("Communication clarity")
        if interview_scores.get('technical_score', 5) < 3:
            improvements.append("Technical depth")
        if interview_scores.get('problem_solving_score', 5) < 3:
            improvements.append("Structured problem-solving")
        
        return improvements or ["No significant areas of concern identified"]
    
    def _extract_notable_responses(self, answers: list) -> list:
        """Extract notable interview responses"""
        if not answers or len(answers) < 2:
            return ["Limited interview responses available"]
        
        return [
            f"Question {i+1}: {ans.get('answer', 'No response')[:100]}..."
            for i, ans in enumerate(answers[:3])  # First 3 responses
        ]
    
    def _summarize_assessment_performance(self, assessment_scores: Dict[str, Any]) -> str:
        """Summarize assessment performance"""
        if not assessment_scores.get('completed', False):
            return "Assessment not completed"
        
        score = assessment_scores.get('overall_score', 0)
        
        if score >= 4:
            return "Excellent performance on technical assessment"
        elif score >= 3:
            return "Good performance with minor areas for improvement"
        elif score >= 2:
            return "Adequate performance but needs development"
        else:
            return "Below expectations - requires significant improvement"
    
    def _calculate_session_duration(self, session: InterviewSession) -> int:
        """Calculate session duration in minutes"""
        # Simple calculation - in production, track actual timestamps
        question_count = len(session.answers) if session.answers else 0
        base_time = question_count * 3  # 3 minutes per question average
        
        if session.assessment_result:
            base_time += 45  # Assessment time
        
        return base_time