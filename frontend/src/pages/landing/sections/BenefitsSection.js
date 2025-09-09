import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { 
  Zap, 
  Shield, 
  TrendingUp, 
  Users,
  Clock,
  Target,
  CheckCircle,
  ArrowRight
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

const BenefitsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 40px;
  margin-bottom: 80px;
  
  @media (max-width: 968px) {
    grid-template-columns: 1fr;
    gap: 32px;
  }
`;

const BenefitCard = styled(motion.div)`
  position: relative;
  padding: 40px 32px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  backdrop-filter: blur(10px);
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(16, 185, 129, 0.1));
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: -1;
  }
  
  &:hover::before {
    opacity: 1;
  }
`;

const BenefitIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, #06b6d4, #10b981);
  color: white;
  margin-bottom: 24px;
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

const BenefitTitle = styled.h3`
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: white;
`;

const BenefitDescription = styled.p`
  font-size: 1rem;
  color: #94a3b8;
  margin: 0 0 24px 0;
  line-height: 1.6;
`;

const BenefitFeatures = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const Feature = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.95rem;
  color: #06b6d4;
`;

const FeatureIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  flex-shrink: 0;
`;

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 32px;
  margin-top: 60px;
  
  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 24px;
  }
  
  @media (max-width: 480px) {
    grid-template-columns: 1fr;
  }
`;

const StatCard = styled(motion.div)`
  text-align: center;
  padding: 32px 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
`;

const StatIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #06b6d4, #10b981);
  color: white;
  margin: 0 auto 16px;
`;

const StatNumber = styled.div`
  font-size: 2rem;
  font-weight: 700;
  color: #06b6d4;
  margin-bottom: 8px;
`;

const StatLabel = styled.div`
  font-size: 0.95rem;
  color: #94a3b8;
  font-weight: 500;
`;

const CTA = styled(motion.div)`
  text-align: center;
  margin-top: 60px;
`;

const CTAButton = styled(motion.button)`
  display: inline-flex;
  align-items: center;
  gap: 12px;
  background: linear-gradient(135deg, #06b6d4 0%, #10b981 100%);
  border: none;
  border-radius: 16px;
  padding: 20px 40px;
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 20px 40px rgba(6, 182, 212, 0.3);
  }
`;

const BenefitsSection = () => {
  const benefits = [
    {
      icon: Zap,
      title: "Мгновенная скорость",
      description: "Создавайте контент в 10 раз быстрее с помощью AI-агентов, которые работают параллельно",
      features: [
        "Создание поста за 2 минуты",
        "Параллельная обработка",
        "Автоматическая оптимизация",
        "Мгновенная публикация"
      ]
    },
    {
      icon: Shield,
      title: "Высокое качество",
      description: "AI проверяет факты, адаптирует под платформы и оптимизирует для максимальной вовлеченности",
      features: [
        "Проверка фактов",
        "SEO оптимизация",
        "Адаптация под платформы",
        "Контроль качества"
      ]
    },
    {
      icon: TrendingUp,
      title: "Масштабируемость",
      description: "От 1 до 1000 постов в месяц - система автоматически адаптируется под ваши потребности",
      features: [
        "Неограниченные объемы",
        "Автоматическое масштабирование",
        "Гибкие тарифы",
        "Эластичная инфраструктура"
      ]
    },
    {
      icon: Users,
      title: "Простота использования",
      description: "Интуитивный интерфейс и автоматизация всех процессов - просто опишите задачу",
      features: [
        "Простой интерфейс",
        "Автоматизация процессов",
        "Готовые шаблоны",
        "Поддержка 24/7"
      ]
    }
  ];

  const stats = [
    {
      icon: Clock,
      number: "95%",
      label: "Экономия времени"
    },
    {
      icon: Target,
      number: "3x",
      label: "Рост вовлеченности"
    },
    {
      icon: CheckCircle,
      number: "99%",
      label: "Точность публикаций"
    },
    {
      icon: TrendingUp,
      number: "10x",
      label: "Увеличение объемов"
    }
  ];

  return (
    <Section>
      <SectionHeader>
        <SectionTitle>
          Почему выбирают нас
        </SectionTitle>
        <SectionSubtitle>
          4 ключевых преимущества, которые делают AI Content Orchestrator незаменимым
        </SectionSubtitle>
      </SectionHeader>

      <BenefitsGrid>
        {benefits.map((benefit, index) => (
          <BenefitCard
            key={index}
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.2 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.02 }}
          >
            <BenefitIcon>
              <benefit.icon size={40} />
            </BenefitIcon>
            <BenefitTitle>{benefit.title}</BenefitTitle>
            <BenefitDescription>{benefit.description}</BenefitDescription>
            <BenefitFeatures>
              {benefit.features.map((feature, featureIndex) => (
                <Feature key={featureIndex}>
                  <FeatureIcon>
                    <CheckCircle size={16} />
                  </FeatureIcon>
                  {feature}
                </Feature>
              ))}
            </BenefitFeatures>
          </BenefitCard>
        ))}
      </BenefitsGrid>

      <StatsContainer>
        {stats.map((stat, index) => (
          <StatCard
            key={index}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.05 }}
          >
            <StatIcon>
              <stat.icon size={28} />
            </StatIcon>
            <StatNumber>{stat.number}</StatNumber>
            <StatLabel>{stat.label}</StatLabel>
          </StatCard>
        ))}
      </StatsContainer>

      <CTA
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        viewport={{ once: true }}
      >
        <CTAButton
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          Попробовать бесплатно
          <ArrowRight size={20} />
        </CTAButton>
      </CTA>
    </Section>
  );
};

export default BenefitsSection;
