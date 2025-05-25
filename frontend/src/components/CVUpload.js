import React, { useState } from 'react';
import { apiClient } from '../services/api';

const CVUpload = ({ sessionId, onCVUploaded }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    validateAndSetFile(file);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const validateAndSetFile = (file) => {
    setError(null);
    
    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
      setError('Please upload a PDF, DOC, DOCX, or TXT file');
      return;
    }

    // Validate file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      setError('File size must be less than 5MB');
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const response = await apiClient.uploadCV(sessionId, selectedFile);
      
      if (response.status === 'success') {
        onCVUploaded({
          summary: response.cv_summary,
          questionsGenerated: response.questions_generated,
          fileName: selectedFile.name
        });
      } else {
        throw new Error('Upload failed');
      }
    } catch (err) {
      setError('Failed to upload and process CV. Please try again.');
      console.error('CV upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setError(null);
  };

  return (
    <div className="cv-upload-container">
      <div className="upload-header">
        <h2>Upload Your CV/Resume</h2>
        <p>Upload your CV to get started with the AI interview process. We'll analyze your background and generate personalized questions.</p>
      </div>

      <div 
        className={`file-upload-area ${dragActive ? 'drag-active' : ''} ${selectedFile ? 'has-file' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {!selectedFile ? (
          <>
            <div className="upload-icon">📄</div>
            <div className="upload-text">
              <p><strong>Drag and drop your CV here</strong></p>
              <p>or</p>
              <label htmlFor="file-input" className="file-input-label">
                Choose File
              </label>
              <input
                id="file-input"
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
            </div>
            <div className="upload-info">
              <p>Supported formats: PDF, DOC, DOCX, TXT</p>
              <p>Maximum size: 5MB</p>
            </div>
          </>
        ) : (
          <div className="file-selected">
            <div className="file-info">
              <div className="file-icon">✓</div>
              <div className="file-details">
                <p className="file-name">{selectedFile.name}</p>
                <p className="file-size">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <button 
                onClick={removeFile}
                className="remove-file-btn"
                disabled={uploading}
              >
                ✕
              </button>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {selectedFile && (
        <div className="upload-actions">
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="upload-button primary"
          >
            {uploading ? (
              <>
                <span className="spinner small"></span>
                Processing CV...
              </>
            ) : (
              'Start Interview Process'
            )}
          </button>
        </div>
      )}

      <div className="upload-tips">
        <h3>Tips for better results:</h3>
        <ul>
          <li>Include detailed work experience and accomplishments</li>
          <li>List relevant technical skills and technologies</li>
          <li>Mention specific projects and their outcomes</li>
          <li>Ensure contact information is clearly visible</li>
        </ul>
      </div>
    </div>
  );
};

export default CVUpload;