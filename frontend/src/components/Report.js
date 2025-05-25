import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';

const Report = ({ sessionId, sessionData }) => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    generateReport();
  }, []);

  const generateReport = async () => {
    try {
      setLoading(true);
      const response = await apiClient.generateReport(sessionId);
      setReport(response);
    } catch (err) {
      setError('Failed to generate report. Please try again.');
      console.error('Report generation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 4) return '#22c55e'; // Green
    if (score >= 3) return '#eab308'; // Yellow
    return '#ef4444'; // Red
  };

  const getRecommendationColor = (recommendation) => {
    switch (recommendation) {
      case 'Strong Hire': return '#22c55e';
      case 'Hire': return '#16a34a';
      case 'Maybe': return '#eab308';
      case 'No Hire': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const downloadReport = () => {
    const reportContent = JSON.stringify(report, null, 2);
    const blob = new Blob([reportContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `interview-report-${sessionId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Generating your evaluation report...</p>
        <p className="loading-detail">This may take a moment as we analyze your responses...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="error-container">
        <h2>Report Generation Failed</h2>
        <p>{error || 'Unable to generate report at this time.'}</p>
        <button onClick={generateReport} className="retry-button">
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="report-container">
      <div className="report-header">
        <h1>Evaluation Report</h1>
        <div className="report-meta">
          <p>Candidate: <strong>{report.candidate_info?.name || 'Unknown'}</strong></p>
          <p>Role: <strong>{report.candidate_info?.role_applied || 'General'}</strong></p>
          <p>Date: <strong>{new Date(report.candidate_info?.evaluation_date).toLocaleDateString() || 'Today'}</strong></p>
        </div>
        <button onClick={downloadReport} className="download-button">
          📄 Download Report
        </button>
      </div>

      {/* Overall Recommendation */}
      <div className="recommendation-section">
        <div className="recommendation-card">
          <div className="recommendation-header">
            <h2>Overall Recommendation</h2>
            <div 
              className="recommendation-badge"
              style={{ backgroundColor: getRecommendationColor(report.recommendation?.decision) }}
            >
              {report.recommendation?.decision || 'Pending'}
            </div>
          </div>
          
          <div className="overall-score">
            <div className="score-circle">
              <span className="score-number">{report.overall_evaluation?.overall_score || 'N/A'}</span>
              <span className="score-label">/ 5</span>
            </div>
          </div>
          
          <div className="recommendation-details">
            <p className="recommendation-reasoning">
              {report.recommendation?.reasoning || 'Evaluation completed successfully.'}
            </p>
            <p className="confidence-level">
              <strong>Confidence Level:</strong> {report.recommendation?.confidence_score || 'Medium'}
            </p>
          </div>
        </div>
      </div>

      {/* Score Breakdown */}
      <div className="scores-section">
        <h2>Score Breakdown</h2>
        
        <div className="scores-grid">
          {/* Interview Scores */}
          <div className="score-category">
            <h3>Interview Performance</h3>
            <div className="score-items">
              {Object.entries(report.interview_evaluation?.scores || {}).map(([key, value]) => {
                if (key === 'detailed_feedback' || key === 'overall_interview_score') return null;
                
                const displayName = key.replace('_score', '').replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
                
                return (
                  <div key={key} className="score-item">
                    <div className="score-info">
                      <span className="score-name">{displayName}</span>
                      <span className="score-value" style={{ color: getScoreColor(value) }}>
                        {value}/5
                      </span>
                    </div>
                    <div className="score-bar">
                      <div 
                        className="score-fill"
                        style={{ 
                          width: `${(value / 5) * 100}%`,
                          backgroundColor: getScoreColor(value)
                        }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Assessment Scores */}
          {report.assessment_evaluation?.completed && (
            <div className="score-category">
              <h3>Assessment Performance</h3>
              <div className="score-items">
                {Object.entries(report.assessment_evaluation?.scores || {}).map(([key, value]) => {
                  if (key === 'completed' || key === 'overall_score') return null;
                  
                  const displayName = key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
                  
                  return (
                    <div key={key} className="score-item">
                      <div className="score-info">
                        <span className="score-name">{displayName}</span>
                        <span className="score-value" style={{ color: getScoreColor(value) }}>
                          {value}/5
                        </span>
                      </div>
                      <div className="score-bar">
                        <div 
                          className="score-fill"
                          style={{ 
                            width: `${(value / 5) * 100}%`,
                            backgroundColor: getScoreColor(value)
                          }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Detailed Analysis */}
      <div className="analysis-section">
        <div className="analysis-grid">
          {/* Strengths */}
          <div className="analysis-card strengths">
            <h3>🎯 Key Strengths</h3>
            <ul>
              {report.interview_evaluation?.strengths?.map((strength, index) => (
                <li key={index}>{strength}</li>
              )) || <li>Analysis in progress</li>}
            </ul>
          </div>

          {/* Areas for Improvement */}
          <div className="analysis-card improvements">
            <h3>📈 Areas for Improvement</h3>
            <ul>
              {report.interview_evaluation?.areas_for_improvement?.map((area, index) => (
                <li key={index}>{area}</li>
              )) || <li>No significant areas identified</li>}
            </ul>
          </div>

          {/* CV Analysis */}
          <div className="analysis-card cv-analysis">
            <h3>📄 CV Analysis</h3>
            <div className="cv-details">
              <p><strong>Experience:</strong> {report.cv_analysis?.experience_years || 0} years</p>
              <p><strong>Education:</strong> {report.cv_analysis?.education_level || 'Not specified'}</p>
              <div className="skills-section">
                <p><strong>Key Skills:</strong></p>
                <div className="skills-tags">
                  {report.cv_analysis?.key_skills?.slice(0, 6).map((skill, index) => (
                    <span key={index} className="skill-tag">{skill}</span>
                  )) || <span className="skill-tag">No skills listed</span>}
                </div>
              </div>
            </div>
          </div>

          {/* Technologies */}
          <div className="analysis-card technologies">
            <h3>💻 Technologies</h3>
            <div className="tech-tags">
              {report.cv_analysis?.technologies?.slice(0, 8).map((tech, index) => (
                <span key={index} className="tech-tag">{tech}</span>
              )) || <span className="tech-tag">No technologies listed</span>}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Feedback */}
      {report.interview_evaluation?.scores?.detailed_feedback && (
        <div className="feedback-section">
          <h2>Detailed Feedback</h2>
          <div className="feedback-grid">
            {Object.entries(report.interview_evaluation.scores.detailed_feedback).map(([category, feedback]) => (
              <div key={category} className="feedback-item">
                <h4>{category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                <p>{feedback}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next Steps */}
      <div className="next-steps-section">
        <h2>Recommended Next Steps</h2>
        <div className="next-steps-list">
          {report.next_steps?.map((step, index) => (
            <div key={index} className="next-step-item">
              <span className="step-number">{index + 1}</span>
              <span className="step-text">{step}</span>
            </div>
          )) || <div className="next-step-item">
            <span className="step-number">1</span>
            <span className="step-text">Manual review required</span>
          </div>}
        </div>
      </div>

      {/* Session Metadata */}
      <div className="metadata-section">
        <h3>Session Information</h3>
        <div className="metadata-grid">
          <div className="metadata-item">
            <span className="metadata-label">Session ID:</span>
            <span className="metadata-value">{report.session_metadata?.session_id || sessionId}</span>
          </div>
          <div className="metadata-item">
            <span className="metadata-label">Duration:</span>
            <span className="metadata-value">{report.session_metadata?.duration_minutes || 0} minutes</span>
          </div>
          <div className="metadata-item">
            <span className="metadata-label">Questions Answered:</span>
            <span className="metadata-value">{report.interview_evaluation?.questions_answered || 0}</span>
          </div>
          <div className="metadata-item">
            <span className="metadata-label">Assessment:</span>
            <span className="metadata-value">
              {report.assessment_evaluation?.completed ? 'Completed' : 'Not completed'}
            </span>
          </div>
        </div>
      </div>

      <div className="report-footer">
        <p>This report was generated by AI Recruiter Co-Pilot using the MERIT evaluation framework.</p>
        <p>For questions about this evaluation, please contact your hiring team.</p>
      </div>
    </div>
  );
};

export default Report;