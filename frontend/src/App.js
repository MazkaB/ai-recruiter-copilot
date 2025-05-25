import React, { useState, useEffect } from 'react';
import CVUpload from './components/CVUpload';
import Interview from './components/Interview';
import Assessment from './components/Assessment';
import Report from './components/Report';
import { apiClient } from './services/api';
import './styles/App.css';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [currentStage, setCurrentStage] = useState('upload'); // upload, interview, assessment, report
  const [sessionData, setSessionData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initialize session on component mount
  useEffect(() => {
    initializeSession();
  }, []);

  const initializeSession = async () => {
    try {
      setLoading(true);
      const response = await apiClient.startSession();
      setSessionId(response.session_id);
      setError(null);
    } catch (err) {
      setError('Failed to initialize session. Please refresh the page.');
      console.error('Session initialization error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCVUploaded = (cvData) => {
    setSessionData(prev => ({ ...prev, cvData }));
    setCurrentStage('interview');
  };

  const handleInterviewComplete = (interviewData) => {
    setSessionData(prev => ({ ...prev, interviewData }));
    setCurrentStage('assessment');
  };

  const handleAssessmentComplete = (assessmentData) => {
    setSessionData(prev => ({ ...prev, assessmentData }));
    setCurrentStage('report');
  };

  const handleSkipAssessment = () => {
    setCurrentStage('report');
  };

  const renderCurrentStage = () => {
    if (loading) {
      return (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Setting up your interview session...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="error-container">
          <h2>Something went wrong</h2>
          <p>{error}</p>
          <button onClick={initializeSession} className="retry-button">
            Try Again
          </button>
        </div>
      );
    }

    if (!sessionId) {
      return (
        <div className="loading-container">
          <p>Initializing session...</p>
        </div>
      );
    }

    switch (currentStage) {
      case 'upload':
        return (
          <CVUpload 
            sessionId={sessionId}
            onCVUploaded={handleCVUploaded}
          />
        );
      
      case 'interview':
        return (
          <Interview 
            sessionId={sessionId}
            cvData={sessionData.cvData}
            onInterviewComplete={handleInterviewComplete}
          />
        );
      
      case 'assessment':
        return (
          <Assessment 
            sessionId={sessionId}
            onAssessmentComplete={handleAssessmentComplete}
            onSkip={handleSkipAssessment}
          />
        );
      
      case 'report':
        return (
          <Report 
            sessionId={sessionId}
            sessionData={sessionData}
          />
        );
      
      default:
        return <div>Unknown stage</div>;
    }
  };

  const getProgressPercentage = () => {
    const stageOrder = ['upload', 'interview', 'assessment', 'report'];
    const currentIndex = stageOrder.indexOf(currentStage);
    return ((currentIndex + 1) / stageOrder.length) * 100;
  };

  const getStageTitle = () => {
    const titles = {
      upload: 'Upload Your CV',
      interview: 'Voice Interview',
      assessment: 'Skills Assessment',
      report: 'Evaluation Report'
    };
    return titles[currentStage] || 'AI Recruiter Co-Pilot';
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Recruiter Co-Pilot</h1>
        <div className="progress-container">
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${getProgressPercentage()}%` }}
            ></div>
          </div>
          <span className="progress-text">{getStageTitle()}</span>
        </div>
      </header>

      <main className="app-main">
        {renderCurrentStage()}
      </main>

      <footer className="app-footer">
        <p>Session ID: {sessionId}</p>
        <p>AI-powered interview experience</p>
      </footer>
    </div>
  );
}

export default App;