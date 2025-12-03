import React from 'react';
import styled from 'styled-components';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

const ErrorContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 32px;
  background: #f8fafc;
  color: #1e293b;
`;

const ErrorIcon = styled.div`
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32px;
  
  svg {
    width: 40px;
    height: 40px;
    color: #ef4444;
  }
`;

const ErrorTitle = styled.h1`
  font-size: 48px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 16px;
  text-align: center;
`;

const ErrorMessage = styled.p`
  font-size: 18px;
  color: #64748b;
  text-align: center;
  max-width: 600px;
  margin-bottom: 32px;
  line-height: 1.6;
`;

const ErrorDetails = styled.details`
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 32px;
  max-width: 800px;
  width: 100%;
  
  summary {
    cursor: pointer;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 16px;
  }
  
  pre {
    background: #f1f5f9;
    border-radius: 4px;
    padding: 16px;
    overflow-x: auto;
    font-size: 14px;
    color: #64748b;
    white-space: pre-wrap;
    word-break: break-word;
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
`;

const ActionButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  ${props => props.primary ? `
    background: #3b82f6;
    color: white;
    
    &:hover {
      background: #2563eb;
      transform: translateY(-2px);
    }
  ` : `
    background: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    
    &:hover {
      background: #f1f5f9;
      border-color: #3b82f6;
    }
  `}
  
  svg {
    width: 20px;
    height: 20px;
  }
`;

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      errorId: Date.now().toString()
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    // Log error to external service in production
    if (process.env.NODE_ENV === 'production' && process.env.REACT_APP_ENABLE_ERROR_REPORTING === 'true') {
      this.logErrorToService(error, errorInfo);
    }

    this.setState({
      error,
      errorInfo
    });
  }

  logErrorToService = (error, errorInfo) => {
    // Log to Sentry or other error reporting service
    if (window.Sentry) {
      window.Sentry.captureException(error, {
        contexts: {
          react: {
            componentStack: errorInfo.componentStack
          }
        }
      });
    }

    // Log to custom error endpoint
    if (process.env.REACT_APP_API_URL) {
      fetch(`${process.env.REACT_APP_API_URL}/api/v1/errors`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error: error.toString(),
          stack: error.stack,
          componentStack: errorInfo.componentStack,
          errorId: this.state.errorId,
          userAgent: navigator.userAgent,
          url: window.location.href,
          timestamp: new Date().toISOString()
        })
      }).catch(console.error);
    }
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <ErrorContainer>
          <ErrorIcon>
            <AlertTriangle />
          </ErrorIcon>
          
          <ErrorTitle>
            Что-то пошло не так
          </ErrorTitle>
          
          <ErrorMessage>
            Произошла непредвиденная ошибка. Мы уже работаем над её исправлением.
            Попробуйте обновить страницу или вернуться на главную.
          </ErrorMessage>

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <ErrorDetails>
              <summary>Детали ошибки (только в режиме разработки)</summary>
              <pre>
                {this.state.error.toString()}
                {this.state.errorInfo.componentStack}
              </pre>
            </ErrorDetails>
          )}

          <ActionButtons>
            <ActionButton onClick={this.handleRetry}>
              <RefreshCw />
              Попробовать снова
            </ActionButton>
            
            <ActionButton onClick={this.handleReload}>
              <RefreshCw />
              Обновить страницу
            </ActionButton>
            
            <ActionButton primary onClick={this.handleGoHome}>
              <Home />
              На главную
            </ActionButton>
          </ActionButtons>
        </ErrorContainer>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
