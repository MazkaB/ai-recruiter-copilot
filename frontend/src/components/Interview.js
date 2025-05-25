import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../services/api';

const Interview = ({ sessionId, cvData, onInterviewComplete }) => {
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [interviewComplete, setInterviewComplete] = useState(false);
  const [answers, setAnswers] = useState([]);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioRef = useRef(null);

  useEffect(() => {
    loadFirstQuestion();
  }, []);

  const loadFirstQuestion = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getCurrentQuestion(sessionId);
      
      if (response.status === 'interview_complete') {
        setInterviewComplete(true);
        onInterviewComplete({ answers, totalAnswers: answers.length });
        return;
      }

      if (response.question) {
        setCurrentQuestion(response.question);
        setQuestionNumber(response.question_number);
        setTotalQuestions(response.total_questions);
        
        // Auto-play question (but don't block if it fails)
        await playQuestionAudio(response.question);
      } else {
        // No more questions available
        setInterviewComplete(true);
        onInterviewComplete({ answers, totalAnswers: answers.length });
      }
      
    } catch (err) {
      setError('Failed to load questions. Please try again.');
      console.error('Question loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const playQuestionAudio = async (question) => {
    try {
      setIsPlaying(true);
      const audioUrl = await apiClient.getTextToSpeech(sessionId, question);
      
      if (audioRef.current && audioUrl) {
        audioRef.current.src = audioUrl;
        await audioRef.current.play();
      }
    } catch (err) {
      console.error('Audio playback error:', err);
      // Continue without audio - this is not a blocking error
      // User can still read the question and continue
    } finally {
      setIsPlaying(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processRecordedAudio(audioBlob);
        
        // Stop all audio tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setError(null);
      
    } catch (err) {
      setError('Microphone access required for voice interview. Please enable microphone and try again.');
      console.error('Recording start error:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processRecordedAudio = async (audioBlob) => {
    try {
      setLoading(true);
      
      // Convert speech to text
      const transcription = await apiClient.speechToText(sessionId, audioBlob);
      setCurrentAnswer(transcription.text);
      
    } catch (err) {
      setError('Failed to process audio. Please try typing your answer instead.');
      console.error('Speech processing error:', err);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!currentAnswer.trim()) {
      setError('Please provide an answer before continuing.');
      return;
    }

    try {
      setLoading(true);
      
      const answerData = {
        answer: currentAnswer,
        timestamp: new Date().toISOString()
      };

      const response = await apiClient.submitAnswer(sessionId, answerData);
      
      // Store answer locally
      const newAnswer = {
        question: currentQuestion,
        answer: currentAnswer,
        questionNumber
      };
      setAnswers(prev => [...prev, newAnswer]);
      
      // Clear current answer
      setCurrentAnswer('');
      
      // Check if interview is complete
      if (response.interview_complete || !response.next_question_available) {
        setInterviewComplete(true);
        onInterviewComplete({ 
          answers: [...answers, newAnswer], 
          totalAnswers: answers.length + 1 
        });
      } else {
        // Load next question
        await loadFirstQuestion();
      }
      
    } catch (err) {
      setError('Failed to submit answer. Please try again.');
      console.error('Answer submission error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTypedAnswer = (event) => {
    setCurrentAnswer(event.target.value);
  };

  const handleCompleteInterview = async () => {
    try {
      await apiClient.completeInterview(sessionId);
      setInterviewComplete(true);
      onInterviewComplete({ answers, totalAnswers: answers.length });
    } catch (err) {
      console.error('Error completing interview:', err);
      // Force complete anyway
      setInterviewComplete(true);
      onInterviewComplete({ answers, totalAnswers: answers.length });
    }
  };

  const replayQuestion = () => {
    if (currentQuestion) {
      playQuestionAudio(currentQuestion);
    }
  };

  if (interviewComplete) {
    return (
      <div className="interview-complete">
        <div className="completion-icon">🎉</div>
        <h2>Interview Complete!</h2>
        <p>Thank you for completing the voice interview.</p>
        <p>You answered {answers.length} questions.</p>
        <div className="next-step">
          <p>Next, we'll move to the skills assessment phase.</p>
        </div>
      </div>
    );
  }

  if (loading && !currentQuestion) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Preparing your interview questions...</p>
      </div>
    );
  }

  return (
    <div className="interview-container">
      <div className="interview-header">
        <div className="question-progress">
          <span className="question-counter">
            Question {questionNumber} of {totalQuestions}
          </span>
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${(questionNumber / totalQuestions) * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      <div className="question-section">
        <div className="question-header">
          <h2>Interview Question</h2>
          <button 
            onClick={replayQuestion}
            className="replay-button"
            disabled={isPlaying}
          >
            {isPlaying ? '🔊 Playing...' : '🔊 Replay'}
          </button>
        </div>
        
        <div className="question-text">
          <p>{currentQuestion}</p>
        </div>
      </div>

      <div className="answer-section">
        <h3>Your Answer</h3>
        
        <div className="recording-controls">
          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={loading}
            className={`record-button ${isRecording ? 'recording' : ''}`}
          >
            {isRecording ? (
              <>
                <span className="recording-indicator"></span>
                Stop Recording
              </>
            ) : (
              <>
                🎤 Start Recording
              </>
            )}
          </button>
          
          <div className="or-divider">or</div>
        </div>

        <div className="text-input-section">
          <textarea
            value={currentAnswer}
            onChange={handleTypedAnswer}
            placeholder="Type your answer here, or use voice recording above..."
            className="answer-textarea"
            rows="6"
            disabled={loading}
          />
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        <div className="answer-actions">
          <button
            onClick={submitAnswer}
            disabled={loading || !currentAnswer.trim()}
            className="submit-button primary"
          >
            {loading ? (
              <>
                <span className="spinner small"></span>
                Processing...
              </>
            ) : (
              'Submit & Continue'
            )}
          </button>
          
          {questionNumber >= 8 && (
            <button
              onClick={handleCompleteInterview}
              className="complete-button secondary"
              style={{ marginLeft: '1rem' }}
            >
              Complete Interview
            </button>
          )}
        </div>
      </div>

      <div className="interview-tips">
        <h4>Interview Tips:</h4>
        <ul>
          <li>Speak clearly and at a normal pace</li>
          <li>Provide specific examples when possible</li>
          <li>Take your time to think before answering</li>
          <li>If recording fails, you can always type your response</li>
        </ul>
      </div>

      {/* Hidden audio element for playback */}
      <audio ref={audioRef} style={{ display: 'none' }} />
    </div>
  );
};

export default Interview;