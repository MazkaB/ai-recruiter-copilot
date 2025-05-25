from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uuid
import json
from typing import Dict, Any
import asyncio
from datetime import datetime

from config import config
from services.cv_parser import CVParser
from services.interview import InterviewService
from services.voice import VoiceService
from services.assessment import AssessmentService
from services.report import ReportService
from database.supabase_client import SupabaseClient
from models.session import InterviewSession

app = FastAPI(title="AI Recruiter Co-Pilot", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
cv_parser = CVParser()
interview_service = InterviewService()
voice_service = VoiceService()
assessment_service = AssessmentService()
report_service = ReportService()
db = SupabaseClient()

# In-memory session storage (for MVP - replace with Redis in production)
sessions: Dict[str, InterviewSession] = {}

@app.get("/")
async def root():
    return {"message": "AI Recruiter Co-Pilot API", "version": "1.0.0"}

@app.post("/session/start")
async def start_session():
    """Initialize a new interview session"""
    session_id = str(uuid.uuid4())
    session = InterviewSession(session_id=session_id)
    sessions[session_id] = session
    
    # Store in database
    await db.create_session(session.model_dump())
    
    return {"session_id": session_id, "status": "initialized"}

@app.post("/session/{session_id}/upload-cv")
async def upload_cv(session_id: str, file: UploadFile = File(...)):
    """Upload and parse CV"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse CV
        cv_data = await cv_parser.parse_cv(content, file.filename)
        
        # Update session
        session = sessions[session_id]
        session.cv_data = cv_data
        session.status = "cv_uploaded"
        
        # Generate initial questions
        questions = await interview_service.generate_questions(cv_data)
        session.questions = questions
        session.current_question_index = 0
        
        # Update database
        await db.update_session(session_id, session.model_dump())
        
        return {
            "status": "success",
            "cv_summary": cv_data.get("summary", ""),
            "questions_generated": len(questions)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV processing failed: {str(e)}")

@app.get("/session/{session_id}/question")
async def get_current_question(session_id: str):
    """Get current interview question"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Check if interview is already marked as complete
    if session.status == "interview_complete":
        return {"status": "interview_complete"}
    
    # Check if we've exceeded question limits
    answered_questions = len(session.answers) if session.answers else 0
    max_questions = config.MAX_QUESTIONS or 8
    
    if (not session.questions or 
        session.current_question_index >= len(session.questions) or
        answered_questions >= max_questions):
        
        session.status = "interview_complete"
        await db.update_session(session_id, session.model_dump())
        return {"status": "interview_complete"}
    
    current_question = session.questions[session.current_question_index]
    
    return {
        "question": current_question,
        "question_number": session.current_question_index + 1,
        "total_questions": len(session.questions),
        "answered_questions": answered_questions,
        "max_questions": max_questions
    }

@app.post("/session/{session_id}/answer")
async def submit_answer(session_id: str, answer_data: dict):
    """Submit answer to current question"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    answer_text = answer_data.get("answer", "")
    
    # Store answer
    if not session.answers:
        session.answers = []
    
    session.answers.append({
        "question": session.questions[session.current_question_index],
        "answer": answer_text,
        "timestamp": answer_data.get("timestamp")
    })
    
    # Move to next question
    session.current_question_index += 1
    
    # Check if interview should be complete
    # Limit total questions to prevent infinite loop
    max_questions = config.MAX_QUESTIONS or 8
    answered_questions = len(session.answers)
    
    if (session.current_question_index >= len(session.questions) or 
        answered_questions >= max_questions):
        session.status = "interview_complete"
    else:
        # Only generate follow-up if we haven't reached the limit and answer was very short
        if (answered_questions < max_questions - 1 and 
            len(answer_text.split()) < 15):  # Very short answer
            follow_up = await interview_service.generate_followup(session.answers[-1])
            if follow_up:
                session.questions.append(follow_up)
    
    # Update database
    await db.update_session(session_id, session.model_dump())
    
    # Return whether more questions are available
    has_next = (session.current_question_index < len(session.questions) and 
                session.status != "interview_complete")
    
    return {
        "status": "answer_recorded", 
        "next_question_available": has_next,
        "interview_complete": session.status == "interview_complete",
        "questions_answered": answered_questions,
        "total_questions": len(session.questions)
    }

@app.post("/session/{session_id}/complete-interview")
async def complete_interview(session_id: str):
    """Manually complete the interview"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    session.status = "interview_complete"
    
    # Update database
    await db.update_session(session_id, session.model_dump())
    
    return {
        "status": "interview_completed_manually",
        "questions_answered": len(session.answers) if session.answers else 0
    }

@app.post("/session/{session_id}/speech-to-text")
async def speech_to_text(session_id: str, audio: UploadFile = File(...)):
    """Convert speech to text"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        audio_content = await audio.read()
        text = await voice_service.speech_to_text(audio_content)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech to text failed: {str(e)}")

@app.get("/session/{session_id}/text-to-speech")
async def text_to_speech(session_id: str, text: str):
    """Convert text to speech"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        audio_stream = await voice_service.text_to_speech(text)
        if audio_stream is None:
            # TTS failed, return an error response that frontend can handle
            raise HTTPException(status_code=503, detail="Text-to-speech service temporarily unavailable")
        return StreamingResponse(audio_stream, media_type="audio/mpeg")
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Text to speech failed - continuing without audio")

@app.post("/session/{session_id}/start-assessment")
async def start_assessment(session_id: str):
    """Start role-specific assessment"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Generate assessment based on CV and role
    assessment = await assessment_service.generate_assessment(session.cv_data)
    session.assessment = assessment
    session.status = "assessment_active"
    
    await db.update_session(session_id, session.model_dump())
    
    return {"assessment": assessment}

@app.post("/session/{session_id}/submit-assessment")
async def submit_assessment(session_id: str, assessment_data: dict):
    """Submit assessment solution"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    session.assessment_result = assessment_data
    session.status = "assessment_complete"
    
    await db.update_session(session_id, session.model_dump())
    
    return {"status": "assessment_submitted"}

@app.get("/session/{session_id}/report")
async def generate_report(session_id: str):
    """Generate final evaluation report"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Generate comprehensive report
    report = await report_service.generate_report(session)
    session.final_report = report
    session.status = "completed"
    
    await db.update_session(session_id, session.dict())
    
    return report

@app.post("/session/{session_id}/complete-interview")
async def complete_interview(session_id: str):
    """Manually complete the interview"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    session.status = "interview_complete"
    
    # Update database
    await db.update_session(session_id, session.model_dump())
    
    return {
        "status": "interview_completed_manually",
        "questions_answered": len(session.answers) if session.answers else 0
    }

@app.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get current session status"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return {
        "session_id": session_id,
        "status": session.status,
        "progress": {
            "cv_uploaded": bool(session.cv_data),
            "questions_answered": len(session.answers) if session.answers else 0,
            "total_questions": len(session.questions) if session.questions else 0,
            "assessment_complete": bool(session.assessment_result),
            "report_generated": bool(session.final_report)
        }
    }

@app.get("/session/{session_id}/debug")
async def debug_session(session_id: str):
    """Debug endpoint to see session state"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    return {
        "session_id": session_id,
        "status": session.status,
        "current_question_index": session.current_question_index,
        "total_questions": len(session.questions) if session.questions else 0,
        "answers_count": len(session.answers) if session.answers else 0,
        "max_questions": config.MAX_QUESTIONS,
        "questions": session.questions if session.questions else [],
        "last_3_answers": (session.answers[-3:] if session.answers and len(session.answers) >= 3 
                          else session.answers) if session.answers else []
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)