/**
 * Register - Компонент регистрации
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Eye, EyeOff, Mail, Lock, User, Building, Phone, ArrowRight } from 'lucide-react';
import styled from 'styled-components';
import { useAuth } from '../../contexts/AuthContext';

const RegisterContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  padding: 20px;
`;

const RegisterCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 500px;
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

const FormRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  
  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
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

const PasswordToggle = styled.button`
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: color 0.3s ease;
  
  &:hover {
    color: #06b6d4;
  }
`;

const ErrorMessage = styled.span`
  color: #ef4444;
  font-size: 12px;
  margin-top: 4px;
  display: block;
`;

const RegisterButton = styled.button`
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

const Divider = styled.div`
  display: flex;
  align-items: center;
  margin: 20px 0;
  
  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
  }
  
  span {
    color: #64748b;
    padding: 0 16px;
    font-size: 14px;
  }
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

const TermsText = styled.p`
  color: #64748b;
  font-size: 12px;
  text-align: center;
  margin-top: 16px;
  line-height: 1.5;
  
  a {
    color: #06b6d4;
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
`;

function Register() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const { register: registerUser, isLoading, error } = useAuth();
  const navigate = useNavigate();
  
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors }
  } = useForm();

  const password = watch('password');

  const onSubmit = async (data) => {
    const result = await registerUser({
      email: data.email,
      password: data.password,
      username: data.username,
      first_name: data.first_name,
      last_name: data.last_name,
      company: data.company,
      phone: data.phone
    });
    
    if (result.success) {
      navigate('/login', { 
        state: { 
          message: 'Регистрация успешна! Проверьте email для подтверждения.' 
        } 
      });
    }
  };

  return (
    <RegisterContainer>
      <RegisterCard>
        <Logo>
          <h1>AI Content Orchestrator</h1>
          <p>Создайте новый аккаунт</p>
        </Logo>

        <Form onSubmit={handleSubmit(onSubmit)}>
          <FormRow>
            <FormGroup>
              <Label>Имя</Label>
              <InputContainer>
                <InputIcon>
                  <User size={20} />
                </InputIcon>
                <Input
                  type="text"
                  placeholder="Введите ваше имя"
                  error={errors.first_name}
                  {...register('first_name', {
                    required: 'Имя обязательно',
                    minLength: {
                      value: 2,
                      message: 'Имя должно содержать минимум 2 символа'
                    }
                  })}
                />
              </InputContainer>
              {errors.first_name && (
                <ErrorMessage>{errors.first_name.message}</ErrorMessage>
              )}
            </FormGroup>

            <FormGroup>
              <Label>Фамилия</Label>
              <InputContainer>
                <InputIcon>
                  <User size={20} />
                </InputIcon>
                <Input
                  type="text"
                  placeholder="Введите вашу фамилию"
                  error={errors.last_name}
                  {...register('last_name', {
                    required: 'Фамилия обязательна',
                    minLength: {
                      value: 2,
                      message: 'Фамилия должна содержать минимум 2 символа'
                    }
                  })}
                />
              </InputContainer>
              {errors.last_name && (
                <ErrorMessage>{errors.last_name.message}</ErrorMessage>
              )}
            </FormGroup>
          </FormRow>

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

          <FormGroup>
            <Label>Имя пользователя</Label>
            <InputContainer>
              <InputIcon>
                <User size={20} />
              </InputIcon>
              <Input
                type="text"
                placeholder="Введите имя пользователя"
                error={errors.username}
                {...register('username', {
                  required: 'Имя пользователя обязательно',
                  minLength: {
                    value: 3,
                    message: 'Имя пользователя должно содержать минимум 3 символа'
                  },
                  pattern: {
                    value: /^[a-zA-Z0-9_]+$/,
                    message: 'Имя пользователя может содержать только буквы, цифры и подчеркивания'
                  }
                })}
              />
            </InputContainer>
            {errors.username && (
              <ErrorMessage>{errors.username.message}</ErrorMessage>
            )}
          </FormGroup>

          <FormRow>
            <FormGroup>
              <Label>Компания</Label>
              <InputContainer>
                <InputIcon>
                  <Building size={20} />
                </InputIcon>
                <Input
                  type="text"
                  placeholder="Название компании"
                  error={errors.company}
                  {...register('company')}
                />
              </InputContainer>
            </FormGroup>

            <FormGroup>
              <Label>Телефон</Label>
              <InputContainer>
                <InputIcon>
                  <Phone size={20} />
                </InputIcon>
                <Input
                  type="tel"
                  placeholder="+7 (999) 123-45-67"
                  error={errors.phone}
                  {...register('phone', {
                    pattern: {
                      value: /^[\+]?[1-9][\d]{0,15}$/,
                      message: 'Неверный формат телефона'
                    }
                  })}
                />
              </InputContainer>
              {errors.phone && (
                <ErrorMessage>{errors.phone.message}</ErrorMessage>
              )}
            </FormGroup>
          </FormRow>

          <FormGroup>
            <Label>Пароль</Label>
            <InputContainer>
              <InputIcon>
                <Lock size={20} />
              </InputIcon>
              <Input
                type={showPassword ? 'text' : 'password'}
                placeholder="Введите пароль"
                error={errors.password}
                {...register('password', {
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
              <PasswordToggle
                type="button"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </PasswordToggle>
            </InputContainer>
            {errors.password && (
              <ErrorMessage>{errors.password.message}</ErrorMessage>
            )}
          </FormGroup>

          <FormGroup>
            <Label>Подтверждение пароля</Label>
            <InputContainer>
              <InputIcon>
                <Lock size={20} />
              </InputIcon>
              <Input
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="Подтвердите пароль"
                error={errors.confirm_password}
                {...register('confirm_password', {
                  required: 'Подтверждение пароля обязательно',
                  validate: value => value === password || 'Пароли не совпадают'
                })}
              />
              <PasswordToggle
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </PasswordToggle>
            </InputContainer>
            {errors.confirm_password && (
              <ErrorMessage>{errors.confirm_password.message}</ErrorMessage>
            )}
          </FormGroup>

          {error && (
            <ErrorMessage style={{ textAlign: 'center', marginTop: '8px' }}>
              {error}
            </ErrorMessage>
          )}

          <RegisterButton type="submit" disabled={isLoading}>
            {isLoading ? (
              <LoadingSpinner />
            ) : (
              <>
                Создать аккаунт
                <ArrowRight size={20} />
              </>
            )}
          </RegisterButton>

          <TermsText>
            Регистрируясь, вы соглашаетесь с{' '}
            <Link to="/terms">условиями использования</Link> и{' '}
            <Link to="/privacy">политикой конфиденциальности</Link>
          </TermsText>

          <Divider>
            <span>или</span>
          </Divider>

          <LinkContainer>
            <Link to="/login">
              Уже есть аккаунт? Войти
            </Link>
          </LinkContainer>
        </Form>
      </RegisterCard>
    </RegisterContainer>
  );
}

export default Register;
