import React from 'react';
import styled from 'styled-components';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

const ErrorContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: ${props => props.theme.spacing.xl};
  background: ${props => props.theme.colors.background};
  color: ${props => props.theme.colors.text};
`;

const ErrorIcon = styled.div`
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: ${props => props.theme.colors.error}20;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: ${props => props.theme.spacing.xl};
  
  svg {
    width: 40px;
    height: 40px;
    color: ${props => props.theme.colors.error};
  }
`;

const ErrorTitle = styled.h1`
  font-size: ${props => props.theme.fontSize.xxl};
  font-weight: ${props => props.theme.fontWeight.bold};
  color: ${props => props.theme.colors.text};
  margin-bottom: ${props => props.theme.spacing.md};
  text-align: center;
`;

const ErrorMessage = styled.p`
  font-size: ${props => props.theme.fontSize.lg};
  color: ${props => props.theme.colors.textSecondary};
  text-align: center;
  max-width: 600px;
  margin-bottom: ${props => props.theme.spacing.xl};
  line-height: 1.6;
`;

const ErrorDetails = styled.details`
  background: ${props => props.theme.colors.backgroundSecondary};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  padding: ${props => props.theme.spacing.lg};
  margin-bottom: ${props => props.theme.spacing.xl};
  max-width: 800px;
  width: 100%;
  
  summary {
    cursor: pointer;
    font-weight: ${props => props.theme.fontWeight.semibold};
    color: ${props => props.theme.colors.text};
    margin-bottom: ${props => props.theme.spacing.md};
  }
  
  pre {
    background: ${props => props.theme.colors.backgroundTertiary};
    border-radius: ${props => props.theme.borderRadius.sm};
    padding: ${props => props.theme.spacing.md};
    overflow-x: auto;
    font-size: ${props => props.theme.fontSize.sm};
    color: ${props => props.theme.colors.textSecondary};
    white-space: pre-wrap;
    word-break: break-word;
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.md};
  flex-wrap: wrap;
  justify-content: center;
`;

const ActionButton = styled.button`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  padding: ${props => props.theme.spacing.md} ${props => props.theme.spacing.lg};
  border: none;
  border-radius: ${props => props.theme.borderRadius.md};
  font-size: ${props => props.theme.fontSize.md};
  font-weight: ${props => props.theme.fontWeight.medium};
  cursor: pointer;
  transition: all ${props => props.theme.transitions.normal};
  
  ${props => props.primary ? `
    background: ${props.theme.colors.primary};
    color: white;
    
    &:hover {
      background: ${props.theme.colors.primaryHover};
      transform: translateY(-2px);
    }
  ` : `
    background: ${props.theme.colors.backgroundSecondary};
    color: ${props.theme.colors.text};
    border: 1px solid ${props.theme.colors.border};
    
    &:hover {
      background: ${props.theme.colors.backgroundTertiary};
      border-color: ${props.theme.colors.primary};
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
