from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class InterviewSession(BaseModel):
    session_id: str
    created_at: datetime = datetime.now()
    status: str = "initialized"  # initialized, cv_uploaded, interview_active, interview_complete, assessment_active, assessment_complete, completed
    
    # CV Data
    cv_data: Optional[Dict[str, Any]] = None
    
    # Interview Data
    questions: Optional[List[str]] = None
    current_question_index: int = 0
    answers: Optional[List[Dict[str, Any]]] = None
    
    # Assessment Data
    assessment: Optional[Dict[str, Any]] = None
    assessment_result: Optional[Dict[str, Any]] = None
    
    # Final Report
    final_report: Optional[Dict[str, Any]] = None
    
    # Metadata
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    role: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }