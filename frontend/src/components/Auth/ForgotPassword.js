/**
 * ForgotPassword - Компонент для сброса пароля
 */

import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Mail, Lock, ArrowRight, CheckCircle } from 'lucide-react';
import styled from 'styled-components';
import { useAuth } from '../../contexts/AuthContext';

const ForgotContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  padding: 20px;
`;

const ForgotCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
`;

const Logo = styled.div`
  text-align: center;
  margin-bottom: 30px;
  
  h1 {
    color: #06b6d4;
    font-size: 28px;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(135deg, #06b6d4, #10b981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  p {
    color: #94a3b8;
    margin: 8px 0 0 0;
    font-size: 14px;
  }
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const FormGroup = styled.div`
  position: relative;
`;

const Label = styled.label`
  display: block;
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
`;

const InputContainer = styled.div`
  position: relative;
`;

const Input = styled.input`
  width: 100%;
  padding: 12px 16px 12px 44px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid ${props => props.error ? '#ef4444' : 'rgba(255, 255, 255, 0.1)'};
  border-radius: 12px;
  color: #e2e8f0;
  font-size: 16px;
  transition: all 0.3s ease;
  
  &:focus {
    outline: none;
    border-color: #06b6d4;
    box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
  }
  
  &::placeholder {
    color: #64748b;
  }
`;

const InputIcon = styled.div`
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  z-index: 1;
`;

const ErrorMessage = styled.span`
  color: #ef4444;
  font-size: 12px;
  margin-top: 4px;
  display: block;
`;

const SubmitButton = styled.button`
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #06b6d4, #10b981);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
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

const SuccessMessage = styled.div`
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 12px;
  padding: 16px;
  margin: 20px 0;
  color: #6ee7b7;
  font-size: 14px;
  text-align: center;
`;

const LinkContainer = styled.div`
  text-align: center;
  margin-top: 20px;
  
  a {
    color: #06b6d4;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s ease;
    
    &:hover {
      color: #10b981;
    }
  }
`;

const InfoText = styled.p`
  color: #64748b;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 20px 0;
`;

function ForgotPassword() {
  const [searchParams] = useSearchParams();
  const [isSuccess, setIsSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { forgotPassword, resetPassword } = useAuth();
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch
  } = useForm();

  const token = searchParams.get('token');
  const isResetMode = !!token;

  const onSubmit = async (data) => {
    try {
      setIsLoading(true);
      setError('');

      if (isResetMode) {
        // Режим сброса пароля
        const result = await resetPassword(token, data.new_password);
        if (result.success) {
          setIsSuccess(true);
        } else {
          setError(result.error);
        }
      } else {
        // Режим запроса сброса
        const result = await forgotPassword(data.email);
        if (result.success) {
          setIsSuccess(true);
        } else {
          setError(result.error);
        }
      }
    } catch (err) {
      setError('Произошла ошибка. Попробуйте еще раз.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <ForgotContainer>
        <ForgotCard>
          <Logo>
            <h1>AI Content Orchestrator</h1>
          </Logo>
          
          <SuccessMessage>
            <CheckCircle size={24} style={{ marginBottom: '12px' }} />
            {isResetMode ? (
              <>
                <strong>Пароль успешно сброшен!</strong>
                <br />
                Теперь вы можете войти в систему с новым паролем.
              </>
            ) : (
              <>
                <strong>Письмо отправлено!</strong>
                <br />
                Если пользователь с таким email существует, инструкции по сбросу пароля отправлены на указанный адрес.
              </>
            )}
          </SuccessMessage>

          <LinkContainer>
            <Link to="/login">
              Вернуться к входу
            </Link>
          </LinkContainer>
        </ForgotCard>
      </ForgotContainer>
    );
  }

  return (
    <ForgotContainer>
      <ForgotCard>
        <Logo>
          <h1>AI Content Orchestrator</h1>
          <p>{isResetMode ? 'Сброс пароля' : 'Забыли пароль?'}</p>
        </Logo>

        <Form onSubmit={handleSubmit(onSubmit)}>
          {isResetMode ? (
            <>
              <FormGroup>
                <Label>Новый пароль</Label>
                <InputContainer>
                  <InputIcon>
                    <Lock size={20} />
                  </InputIcon>
                  <Input
                    type="password"
                    placeholder="Введите новый пароль"
                    error={errors.new_password}
                    {...register('new_password', {
                      required: 'Пароль обязателен',
                      minLength: {
                        value: 8,
                        message: 'Пароль должен содержать минимум 8 символов'
                      },
                      pattern: {
                        value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
                        message: 'Пароль должен содержать заглавную букву, строчную букву и цифру'
                      }
                    })}
                  />
                </InputContainer>
                {errors.new_password && (
                  <ErrorMessage>{errors.new_password.message}</ErrorMessage>
                )}
              </FormGroup>

              <FormGroup>
                <Label>Подтверждение пароля</Label>
                <InputContainer>
                  <InputIcon>
                    <Lock size={20} />
                  </InputIcon>
                  <Input
                    type="password"
                    placeholder="Подтвердите новый пароль"
                    error={errors.confirm_password}
                    {...register('confirm_password', {
                      required: 'Подтверждение пароля обязательно',
                      validate: value => value === watch('new_password') || 'Пароли не совпадают'
                    })}
                  />
                </InputContainer>
                {errors.confirm_password && (
                  <ErrorMessage>{errors.confirm_password.message}</ErrorMessage>
                )}
              </FormGroup>
            </>
          ) : (
            <>
              <InfoText>
                Введите ваш email адрес, и мы отправим вам инструкции по сбросу пароля.
              </InfoText>

              <FormGroup>
                <Label>Email</Label>
                <InputContainer>
                  <InputIcon>
                    <Mail size={20} />
                  </InputIcon>
                  <Input
                    type="email"
                    placeholder="Введите ваш email"
                    error={errors.email}
                    {...register('email', {
                      required: 'Email обязателен',
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Неверный формат email'
                      }
                    })}
                  />
                </InputContainer>
                {errors.email && (
                  <ErrorMessage>{errors.email.message}</ErrorMessage>
                )}
              </FormGroup>
            </>
          )}

          {error && (
            <ErrorMessage style={{ textAlign: 'center', marginTop: '8px' }}>
              {error}
            </ErrorMessage>
          )}

          <SubmitButton type="submit" disabled={isLoading}>
            {isLoading ? (
              <LoadingSpinner />
            ) : (
              <>
                {isResetMode ? 'Сбросить пароль' : 'Отправить инструкции'}
                <ArrowRight size={20} />
              </>
            )}
          </SubmitButton>

          <LinkContainer>
            <Link to="/login">
              Вернуться к входу
            </Link>
          </LinkContainer>
        </Form>
      </ForgotCard>
    </ForgotContainer>
  );
}

export default ForgotPassword;
