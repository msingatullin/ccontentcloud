/**
 * VerifyEmail - Компонент для верификации email
 */

import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Mail, CheckCircle, XCircle, ArrowRight } from 'lucide-react';
import styled from 'styled-components';
import { useAuth } from '../../contexts/AuthContext';

const VerifyContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  padding: 20px;
`;

const VerifyCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
  text-align: center;
`;

const IconContainer = styled.div`
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  background: ${props => {
    if (props.status === 'success') return 'linear-gradient(135deg, #10b981, #059669)';
    if (props.status === 'error') return 'linear-gradient(135deg, #ef4444, #dc2626)';
    return 'linear-gradient(135deg, #06b6d4, #0891b2)';
  }};
`;

const Title = styled.h1`
  color: #e2e8f0;
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 12px 0;
`;

const Description = styled.p`
  color: #94a3b8;
  font-size: 16px;
  line-height: 1.6;
  margin: 0 0 24px 0;
`;

const ResendButton = styled.button`
  background: linear-gradient(135deg, #06b6d4, #10b981);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  padding: 12px 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(6, 182, 212, 0.3);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;

const ContinueButton = styled.button`
  background: linear-gradient(135deg, #06b6d4, #10b981);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  padding: 14px 28px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(6, 182, 212, 0.3);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;

const LoadingSpinner = styled.div`
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const ErrorMessage = styled.div`
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 12px;
  padding: 16px;
  margin: 20px 0;
  color: #fca5a5;
  font-size: 14px;
`;

const SuccessMessage = styled.div`
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 12px;
  padding: 16px;
  margin: 20px 0;
  color: #6ee7b7;
  font-size: 14px;
`;

function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { verifyEmail, user, resendVerification } = useAuth();
  
  const [status, setStatus] = useState('loading'); // loading, success, error
  const [message, setMessage] = useState('');
  const [isResending, setIsResending] = useState(false);
  
  const token = searchParams.get('token');

  useEffect(() => {
    if (token) {
      handleVerifyEmail(token);
    } else {
      setStatus('error');
      setMessage('Токен верификации не найден');
    }
  }, [token]);

  const handleVerifyEmail = async (verificationToken) => {
    try {
      setStatus('loading');
      const result = await verifyEmail(verificationToken);
      
      if (result.success) {
        setStatus('success');
        setMessage('Email успешно подтвержден! Теперь вы можете пользоваться всеми возможностями системы.');
      } else {
        setStatus('error');
        setMessage(result.error || 'Ошибка при подтверждении email');
      }
    } catch (error) {
      setStatus('error');
      setMessage('Произошла ошибка при подтверждении email');
    }
  };

  const handleResendVerification = async () => {
    if (!user?.email) {
      setMessage('Email пользователя не найден');
      return;
    }

    try {
      setIsResending(true);
      const result = await resendVerification(user.email);
      
      if (result.success) {
        setMessage('Письмо с подтверждением отправлено повторно. Проверьте ваш email.');
      } else {
        setMessage(result.error || 'Ошибка при отправке письма');
      }
    } catch (error) {
      setMessage('Произошла ошибка при отправке письма');
    } finally {
      setIsResending(false);
    }
  };

  const handleContinue = () => {
    navigate('/dashboard');
  };

  const renderContent = () => {
    switch (status) {
      case 'loading':
        return (
          <>
            <IconContainer>
              <Mail size={40} color="white" />
            </IconContainer>
            <Title>Подтверждение email</Title>
            <Description>
              Проверяем ваш токен верификации...
            </Description>
            <LoadingSpinner />
          </>
        );

      case 'success':
        return (
          <>
            <IconContainer status="success">
              <CheckCircle size={40} color="white" />
            </IconContainer>
            <Title>Email подтвержден!</Title>
            <Description>
              {message}
            </Description>
            <SuccessMessage>
              Теперь вы можете пользоваться всеми возможностями AI Content Orchestrator
            </SuccessMessage>
            <ContinueButton onClick={handleContinue}>
              Продолжить
              <ArrowRight size={20} />
            </ContinueButton>
          </>
        );

      case 'error':
        return (
          <>
            <IconContainer status="error">
              <XCircle size={40} color="white" />
            </IconContainer>
            <Title>Ошибка подтверждения</Title>
            <Description>
              {message}
            </Description>
            <ErrorMessage>
              Возможные причины:
              <br />• Токен истек (действителен 24 часа)
              <br />• Токен уже использован
              <br />• Неверный токен
            </ErrorMessage>
            {user?.email && (
              <ResendButton 
                onClick={handleResendVerification}
                disabled={isResending}
              >
                {isResending ? (
                  <LoadingSpinner />
                ) : (
                  <>
                    <Mail size={20} />
                    Отправить повторно
                  </>
                )}
              </ResendButton>
            )}
          </>
        );

      default:
        return null;
    }
  };

  return (
    <VerifyContainer>
      <VerifyCard>
        {renderContent()}
      </VerifyCard>
    </VerifyContainer>
  );
}

export default VerifyEmail;
