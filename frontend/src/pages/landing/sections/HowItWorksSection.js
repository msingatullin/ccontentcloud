import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { 
  Lightbulb, 
  Cpu, 
  Rocket, 
  ArrowRight,
  Brain,
  Target,
  Zap
} from 'lucide-react';

const Section = styled.section`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
`;

const SectionHeader = styled.div`
  text-align: center;
  margin-bottom: 80px;
`;

const SectionTitle = styled.h2`
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 16px 0;
  background: linear-gradient(135deg, #ffffff 0%, #06b6d4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  
  @media (max-width: 768px) {
    font-size: 2rem;
  }
`;

const SectionSubtitle = styled.p`
  font-size: 1.25rem;
  color: #94a3b8;
  margin: 0;
  max-width: 600px;
  margin: 0 auto;
  
  @media (max-width: 768px) {
    font-size: 1.1rem;
  }
`;

const StepsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 40px;
  margin-bottom: 80px;
  
  @media (max-width: 968px) {
    grid-template-columns: 1fr;
    gap: 60px;
  }
`;

const StepCard = styled(motion.div)`
  position: relative;
  text-align: center;
  padding: 40px 24px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(16, 185, 129, 0.1));
    border-radius: 20px;
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: -1;
  }
  
  &:hover::before {
    opacity: 1;
  }
`;

const StepNumber = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, #06b6d4, #10b981);
  color: white;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 auto 24px;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    top: -4px;
    left: -4px;
    right: -4px;
    bottom: -4px;
    background: linear-gradient(135deg, #06b6d4, #10b981);
    border-radius: 24px;
    opacity: 0.3;
    z-index: -1;
  }
`;

const StepIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: rgba(6, 182, 212, 0.1);
  color: #06b6d4;
  margin: 0 auto 24px;
`;

const StepTitle = styled.h3`
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: white;
`;

const StepDescription = styled.p`
  font-size: 1rem;
  color: #94a3b8;
  margin: 0 0 24px 0;
  line-height: 1.6;
`;

const StepFeatures = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
`;

const Feature = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #06b6d4;
  
  &::before {
    content: '✓';
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
    font-size: 0.8rem;
    font-weight: 600;
  }
`;

const Arrow = styled(motion.div)`
  position: absolute;
  right: -20px;
  top: 50%;
  transform: translateY(-50%);
  color: #06b6d4;
  z-index: 10;
  
  @media (max-width: 968px) {
    display: none;
  }
`;

const ProcessFlow = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  margin: 60px 0;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 20px;
  }
`;

const FlowItem = styled(motion.div)`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  min-width: 200px;
`;

const FlowIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #06b6d4, #10b981);
  color: white;
`;

const FlowLabel = styled.div`
  font-size: 0.9rem;
  color: #94a3b8;
  text-align: center;
`;

const FlowArrow = styled(motion.div)`
  color: #06b6d4;
  
  @media (max-width: 768px) {
    transform: rotate(90deg);
  }
`;

const HowItWorksSection = () => {
  const steps = [
    {
      number: 1,
      icon: Lightbulb,
      title: "Загружаете задачу",
      description: "Описываете, какой контент нужен, для какой аудитории и на каких платформах",
      features: [
        "Анализ трендов",
        "Исследование аудитории",
        "Планирование контента"
      ]
    },
    {
      number: 2,
      icon: Cpu,
      title: "AI создает контент",
      description: "10 специализированных агентов работают параллельно над вашим контентом",
      features: [
        "Генерация текстов",
        "Создание изображений",
        "Адаптация под платформы"
      ]
    },
    {
      number: 3,
      icon: Rocket,
      title: "Публикуется автоматически",
      description: "Готовый контент публикуется на всех выбранных платформах по расписанию",
      features: [
        "Автоматическая публикация",
        "Мониторинг результатов",
        "Оптимизация по метрикам"
      ]
    }
  ];

  const processFlow = [
    {
      icon: Brain,
      label: "Анализ задачи"
    },
    {
      icon: Target,
      label: "Создание контента"
    },
    {
      icon: Zap,
      label: "Публикация"
    }
  ];

  return (
    <Section>
      <SectionHeader>
        <SectionTitle>
          Как это работает
        </SectionTitle>
        <SectionSubtitle>
          Простой процесс от идеи до публикации за 3 шага
        </SectionSubtitle>
      </SectionHeader>

      <StepsContainer>
        {steps.map((step, index) => (
          <StepCard
            key={index}
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.2 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.05 }}
          >
            <StepNumber>{step.number}</StepNumber>
            <StepIcon>
              <step.icon size={32} />
            </StepIcon>
            <StepTitle>{step.title}</StepTitle>
            <StepDescription>{step.description}</StepDescription>
            <StepFeatures>
              {step.features.map((feature, featureIndex) => (
                <Feature key={featureIndex}>{feature}</Feature>
              ))}
            </StepFeatures>
            {index < steps.length - 1 && (
              <Arrow
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.2 + 0.5 }}
                viewport={{ once: true }}
              >
                <ArrowRight size={24} />
              </Arrow>
            )}
          </StepCard>
        ))}
      </StepsContainer>

      <ProcessFlow>
        {processFlow.map((item, index) => (
          <React.Fragment key={index}>
            <FlowItem
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.2 }}
              viewport={{ once: true }}
            >
              <FlowIcon>
                <item.icon size={24} />
              </FlowIcon>
              <FlowLabel>{item.label}</FlowLabel>
            </FlowItem>
            {index < processFlow.length - 1 && (
              <FlowArrow
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ delay: index * 0.2 + 0.3 }}
                viewport={{ once: true }}
              >
                <ArrowRight size={20} />
              </FlowArrow>
            )}
          </React.Fragment>
        ))}
      </ProcessFlow>
    </Section>
  );
};

export default HowItWorksSection;
