const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Don't set Content-Type for FormData
    if (options.body instanceof FormData) {
      delete config.headers['Content-Type'];
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      // Handle different response types
      const contentType = response.headers.get('Content-Type');
      
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else if (contentType && contentType.includes('audio/')) {
        return URL.createObjectURL(await response.blob());
      } else {
        return await response.text();
      }
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Session Management
  async startSession() {
    return this.request('/session/start', {
      method: 'POST',
    });
  }

  async getSessionStatus(sessionId) {
    return this.request(`/session/${sessionId}/status`);
  }

  // CV Upload and Processing
  async uploadCV(sessionId, file) {
    const formData = new FormData();
    formData.append('file', file);

    return this.request(`/session/${sessionId}/upload-cv`, {
      method: 'POST',
      body: formData,
    });
  }

  // Interview Management
  async getCurrentQuestion(sessionId) {
    return this.request(`/session/${sessionId}/question`);
  }

  async submitAnswer(sessionId, answerData) {
    return this.request(`/session/${sessionId}/answer`, {
      method: 'POST',
      body: JSON.stringify(answerData),
    });
  }

  async completeInterview(sessionId) {
    return this.request(`/session/${sessionId}/complete-interview`, {
      method: 'POST',
    });
  }

  // Voice Processing
  async speechToText(sessionId, audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

    return this.request(`/session/${sessionId}/speech-to-text`, {
      method: 'POST',
      body: formData,
    });
  }

  async getTextToSpeech(sessionId, text) {
    try {
      const encodedText = encodeURIComponent(text);
      return this.request(`/session/${sessionId}/text-to-speech?text=${encodedText}`);
    } catch (error) {
      // TTS is not critical - log error and return null
      console.warn('Text-to-speech failed:', error.message);
      return null;
    }
  }

  // Assessment Management
  async startAssessment(sessionId) {
    return this.request(`/session/${sessionId}/start-assessment`, {
      method: 'POST',
    });
  }

  async submitAssessment(sessionId, assessmentData) {
    return this.request(`/session/${sessionId}/submit-assessment`, {
      method: 'POST',
      body: JSON.stringify(assessmentData),
    });
  }

  // Report Generation
  async generateReport(sessionId) {
    return this.request(`/session/${sessionId}/report`);
  }

  // Utility Methods
  async ping() {
    return this.request('/');
  }

  // Error handling helper
  handleApiError(error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return {
        message: 'Unable to connect to the server. Please check your connection and try again.',
        type: 'connection_error'
      };
    }
    
    if (error.message.includes('404')) {
      return {
        message: 'Session not found. Please refresh the page and start a new session.',
        type: 'session_error'
      };
    }
    
    if (error.message.includes('500')) {
      return {
        message: 'Server error. Please try again in a moment.',
        type: 'server_error'
      };
    }
    
    return {
      message: error.message || 'An unexpected error occurred.',
      type: 'unknown_error'
    };
  }

  // File validation helpers
  validateFileType(file, allowedTypes = ['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']) {
    return allowedTypes.includes(file.type);
  }

  validateFileSize(file, maxSizeInMB = 5) {
    return file.size <= maxSizeInMB * 1024 * 1024;
  }

  // Audio format validation
  validateAudioFormat(file) {
    const allowedTypes = ['audio/webm', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/ogg'];
    return allowedTypes.includes(file.type);
  }

  // Session data helpers
  getSessionFromStorage(sessionId) {
    try {
      const data = localStorage.getItem(`session_${sessionId}`);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error reading session from storage:', error);
      return null;
    }
  }

  saveSessionToStorage(sessionId, data) {
    try {
      localStorage.setItem(`session_${sessionId}`, JSON.stringify(data));
    } catch (error) {
      console.error('Error saving session to storage:', error);
    }
  }

  clearSessionFromStorage(sessionId) {
    try {
      localStorage.removeItem(`session_${sessionId}`);
    } catch (error) {
      console.error('Error clearing session from storage:', error);
    }
  }

  // Network status helpers
  async checkConnection() {
    try {
      await this.ping();
      return true;
    } catch (error) {
      return false;
    }
  }

  // Rate limiting helper
  createRateLimiter(maxRequests = 10, windowMs = 60000) {
    const requests = [];
    
    return async (requestFn) => {
      const now = Date.now();
      
      // Remove old requests
      while (requests.length > 0 && requests[0] < now - windowMs) {
        requests.shift();
      }
      
      if (requests.length >= maxRequests) {
        throw new Error('Too many requests. Please wait a moment and try again.');
      }
      
      requests.push(now);
      return await requestFn();
    };
  }

  // Retry mechanism
  async requestWithRetry(endpoint, options = {}, maxRetries = 3, delay = 1000) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await this.request(endpoint, options);
      } catch (error) {
        if (attempt === maxRetries) {
          throw error;
        }
        
        // Don't retry on client errors (4xx)
        if (error.message.includes('4')) {
          throw error;
        }
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, delay * attempt));
      }
    }
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export { ApiClient };