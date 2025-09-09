import React, { useState } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { 
  ArrowRight, 
  CheckCircle, 
  Mail, 
  Lock,
  User,
  Building,
  Zap,
  Shield,
  Clock
} from 'lucide-react';
import toast from 'react-hot-toast';

const Section = styled.section`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
`;

const CTAContainer = styled.div`
  position: relative;
  padding: 80px 40px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  border-radius: 32px;
  text-align: center;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(16, 185, 129, 0.1));
    z-index: 1;
  }
  
  @media (max-width: 768px) {
    padding: 60px 20px;
  }
`;

const Content = styled.div`
  position: relative;
  z-index: 2;
`;

const CTATitle = styled.h2`
  font-size: 3rem;
  font-weight: 800;
  margin: 0 0 16px 0;
  background: linear-gradient(135deg, #ffffff 0%, #06b6d4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  
  @media (max-width: 768px) {
    font-size: 2.5rem;
  }
  
  @media (max-width: 480px) {
    font-size: 2rem;
  }
`;

const CTASubtitle = styled.p`
  font-size: 1.25rem;
  color: #94a3b8;
  margin: 0 0 40px 0;
  max-width: 600px;
  margin: 0 auto 40px;
  line-height: 1.6;
  
  @media (max-width: 768px) {
    font-size: 1.1rem;
  }
`;

const FormContainer = styled.div`
  max-width: 500px;
  margin: 0 auto 40px;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const InputGroup = styled.div`
  position: relative;
`;

const Input = styled.input`
  width: 100%;
  padding: 16px 20px 16px 50px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  font-size: 1rem;
  color: white;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  
  &::placeholder {
    color: #94a3b8;
  }
  
  &:focus {
    outline: none;
    border-color: #06b6d4;
    background: rgba(255, 255, 255, 0.15);
  }
  
  &:invalid {
    border-color: #ef4444;
  }
`;

const InputIcon = styled.div`
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  z-index: 1;
`;

const ErrorMessage = styled.div`
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 4px;
  text-align: left;
`;

const SubmitButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #06b6d4 0%, #10b981 100%);
  border: none;
  border-radius: 12px;
  padding: 18px 32px;
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 8px;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 20px 40px rgba(6, 182, 212, 0.3);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
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

const BenefitsList = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 40px;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 16px;
  }
`;

const Benefit = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
`;

const BenefitIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  flex-shrink: 0;
`;

const BenefitText = styled.div`
  font-size: 0.95rem;
  color: #e2e8f0;
  font-weight: 500;
`;

const TrustIndicators = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  margin-top: 40px;
  padding-top: 40px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 16px;
  }
`;

const TrustItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #94a3b8;
`;

const TrustIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
`;

const FinalCTASection = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register, handleSubmit, formState: { errors }, reset } = useForm();

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      // Симуляция отправки данных
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Здесь будет реальная интеграция с API
      console.log('Registration data:', data);
      
      toast.success('Регистрация успешна! Проверьте email для подтверждения.');
      reset();
    } catch (error) {
      console.error('Registration error:', error);
      toast.error('Ошибка регистрации. Попробуйте позже.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const benefits = [
    {
      icon: Zap,
      text: "Начните за 2 минуты"
    },
    {
      icon: Shield,
      text: "Безопасно и надежно"
    },
    {
      icon: Clock,
      text: "7 дней бесплатно"
    }
  ];

  const trustIndicators = [
    {
      icon: Shield,
      text: "SSL защита"
    },
    {
      icon: CheckCircle,
      text: "GDPR совместимость"
    },
    {
      icon: Lock,
      text: "Безопасные платежи"
    }
  ];

  return (
    <Section>
      <CTAContainer>
        <Content>
          <CTATitle>
            Готовы начать?
          </CTATitle>
          <CTASubtitle>
            Присоединяйтесь к тысячам маркетологов, которые уже автоматизировали 
            создание контента с помощью AI
          </CTASubtitle>

          <FormContainer>
            <Form onSubmit={handleSubmit(onSubmit)}>
              <InputGroup>
                <InputIcon>
                  <User size={20} />
                </InputIcon>
                <Input
                  type="text"
                  placeholder="Ваше имя"
                  {...register('name', { 
                    required: 'Имя обязательно',
                    minLength: { value: 2, message: 'Минимум 2 символа' }
                  })}
                />
                {errors.name && <ErrorMessage>{errors.name.message}</ErrorMessage>}
              </InputGroup>

              <InputGroup>
                <InputIcon>
                  <Mail size={20} />
                </InputIcon>
                <Input
                  type="email"
                  placeholder="Email адрес"
                  {...register('email', { 
                    required: 'Email обязателен',
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: 'Некорректный email'
                    }
                  })}
                />
                {errors.email && <ErrorMessage>{errors.email.message}</ErrorMessage>}
              </InputGroup>

              <InputGroup>
                <InputIcon>
                  <Building size={20} />
                </InputIcon>
                <Input
                  type="text"
                  placeholder="Название компании (необязательно)"
                  {...register('company')}
                />
              </InputGroup>

              <SubmitButton
                type="submit"
                disabled={isSubmitting}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {isSubmitting ? (
                  <LoadingSpinner />
                ) : (
                  <>
                    Создать аккаунт бесплатно
                    <ArrowRight size={20} />
                  </>
                )}
              </SubmitButton>
            </Form>
          </FormContainer>

          <BenefitsList>
            {benefits.map((benefit, index) => (
              <Benefit key={index}>
                <BenefitIcon>
                  <benefit.icon size={20} />
                </BenefitIcon>
                <BenefitText>{benefit.text}</BenefitText>
              </Benefit>
            ))}
          </BenefitsList>

          <TrustIndicators>
            {trustIndicators.map((indicator, index) => (
              <TrustItem key={index}>
                <TrustIcon>
                  <indicator.icon size={16} />
                </TrustIcon>
                {indicator.text}
              </TrustItem>
            ))}
          </TrustIndicators>
        </Content>
      </CTAContainer>
    </Section>
  );
};

export default FinalCTASection;
