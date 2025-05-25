import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';

const Assessment = ({ sessionId, onAssessmentComplete, onSkip }) => {
  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [timerActive, setTimerActive] = useState(false);
  const [userSolution, setUserSolution] = useState('');
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    loadAssessment();
  }, []);

  useEffect(() => {
    let interval = null;
    if (timerActive && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining(time => {
          if (time <= 1) {
            setTimerActive(false);
            handleTimeUp();
            return 0;
          }
          return time - 1;
        });
      }, 1000);
    } else if (timeRemaining === 0) {
      setTimerActive(false);
    }
    
    return () => clearInterval(interval);
  }, [timerActive, timeRemaining]);

  const loadAssessment = async () => {
    try {
      setLoading(true);
      const response = await apiClient.startAssessment(sessionId);
      
      setAssessment(response.assessment);
      setTimeRemaining(response.assessment.time_limit * 60); // Convert minutes to seconds
      
      // Set initial code if it's a coding assessment
      if (response.assessment.type === 'coding' && response.assessment.starter_code) {
        setUserSolution(response.assessment.starter_code);
      }
      
    } catch (err) {
      setError('Failed to load assessment. Please try again.');
      console.error('Assessment loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const startAssessment = () => {
    setTimerActive(true);
  };

  const handleTimeUp = () => {
    if (!submitted) {
      submitAssessment();
    }
  };

  const submitAssessment = async () => {
    try {
      setLoading(true);
      setSubmitted(true);
      setTimerActive(false);

      const submissionData = {
        type: assessment.type,
        solution: userSolution,
        submitted_at: new Date().toISOString(),
        time_spent: (assessment.time_limit * 60) - timeRemaining
      };

      await apiClient.submitAssessment(sessionId, submissionData);
      
      onAssessmentComplete({
        type: assessment.type,
        completed: true,
        timeSpent: Math.round(((assessment.time_limit * 60) - timeRemaining) / 60)
      });
      
    } catch (err) {
      setError('Failed to submit assessment. Please try again.');
      console.error('Assessment submission error:', err);
      setLoading(false);
      setSubmitted(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSkipAssessment = () => {
    if (window.confirm('Are you sure you want to skip the assessment? This will affect your evaluation.')) {
      onSkip();
    }
  };

  if (loading && !assessment) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Preparing your assessment...</p>
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="error-container">
        <h2>Assessment Unavailable</h2>
        <p>{error || 'Unable to load assessment at this time.'}</p>
        <div className="assessment-actions">
          <button onClick={loadAssessment} className="retry-button">
            Try Again
          </button>
          <button onClick={handleSkipAssessment} className="skip-button">
            Skip Assessment
          </button>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="assessment-complete">
        <div className="completion-icon">✅</div>
        <h2>Assessment Submitted!</h2>
        <p>Thank you for completing the {assessment.type === 'coding' ? 'coding' : 'skills'} assessment.</p>
        <p>Your response has been recorded and will be evaluated.</p>
        <div className="next-step">
          <p>Proceeding to generate your evaluation report...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="assessment-container">
      <div className="assessment-header">
        <div className="assessment-info">
          <h2>{assessment.title}</h2>
          <div className="assessment-meta">
            <span className="assessment-type">
              {assessment.type === 'coding' ? '💻 Coding' : 
               assessment.type === 'business_case' ? '💼 Business' : 
               '📝 Analytical'} Assessment
            </span>
            <span className="time-limit">⏱️ {assessment.time_limit} minutes</span>
          </div>
        </div>

        {timerActive && (
          <div className={`timer ${timeRemaining <= 300 ? 'warning' : ''}`}>
            <div className="timer-display">
              {formatTime(timeRemaining)}
            </div>
            <div className="timer-label">Remaining</div>
          </div>
        )}
      </div>

      {!timerActive ? (
        <div className="assessment-intro">
          <div className="description-section">
            <h3>Assessment Description</h3>
            <p>{assessment.description}</p>
            
            {assessment.scenario && (
              <div className="scenario-section">
                <h4>Scenario</h4>
                <p>{assessment.scenario.context}</p>
                {assessment.scenario.problem && (
                  <div className="problem-statement">
                    <strong>Problem:</strong> {assessment.scenario.problem}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="requirements-section">
            <h3>Requirements</h3>
            <ul>
              {assessment.requirements.map((req, index) => (
                <li key={index}>{req}</li>
              ))}
            </ul>
          </div>

          {assessment.example_input && (
            <div className="example-section">
              <h4>Example</h4>
              <div className="example-box">
                <p><strong>Input:</strong> {assessment.example_input}</p>
                <p><strong>Expected Output:</strong> {assessment.example_output}</p>
              </div>
            </div>
          )}

          <div className="assessment-actions">
            <button onClick={startAssessment} className="start-button primary">
              Start Assessment ({assessment.time_limit} min)
            </button>
            <button onClick={handleSkipAssessment} className="skip-button secondary">
              Skip Assessment
            </button>
          </div>
        </div>
      ) : (
        <div className="assessment-work-area">
          <div className="problem-summary">
            <h3>{assessment.title}</h3>
            <p>{assessment.description}</p>
          </div>

          <div className="solution-area">
            <div className="solution-header">
              <h3>Your Solution</h3>
              {assessment.language && (
                <span className="language-tag">{assessment.language}</span>
              )}
            </div>
            
            <textarea
              value={userSolution}
              onChange={(e) => setUserSolution(e.target.value)}
              placeholder={
                assessment.type === 'coding' 
                  ? "Write your code solution here..."
                  : "Provide your detailed response here..."
              }
              className="solution-textarea"
              rows="20"
            />
          </div>

          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}

          <div className="assessment-actions">
            <button
              onClick={submitAssessment}
              disabled={loading || !userSolution.trim()}
              className="submit-button primary"
            >
              {loading ? (
                <>
                  <span className="spinner small"></span>
                  Submitting...
                </>
              ) : (
                'Submit Solution'
              )}
            </button>
          </div>
        </div>
      )}

      <div className="assessment-tips">
        <h4>Tips:</h4>
        <ul>
          <li>Read the requirements carefully before starting</li>
          <li>Plan your approach before writing code/solution</li>
          <li>Test your solution with the provided examples</li>
          <li>Submit before time runs out - partial solutions are better than none</li>
          {assessment.type === 'coding' && (
            <li>Focus on correctness first, then optimize if time allows</li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default Assessment;