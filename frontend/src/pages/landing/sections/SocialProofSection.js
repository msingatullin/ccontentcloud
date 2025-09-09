import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { 
  Star, 
  Quote, 
  TrendingUp, 
  Users,
  Award,
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

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 32px;
  margin-bottom: 80px;
  
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
  font-size: 2.5rem;
  font-weight: 700;
  color: #06b6d4;
  margin-bottom: 8px;
`;

const StatLabel = styled.div`
  font-size: 1rem;
  color: #94a3b8;
  font-weight: 500;
`;

const TestimonialsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
  margin-bottom: 80px;
  
  @media (max-width: 968px) {
    grid-template-columns: 1fr;
    gap: 24px;
  }
`;

const TestimonialCard = styled(motion.div)`
  position: relative;
  padding: 32px 24px;
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
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: -1;
    border-radius: 20px;
  }
  
  &:hover::before {
    opacity: 1;
  }
`;

const QuoteIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(6, 182, 212, 0.1);
  color: #06b6d4;
  margin-bottom: 20px;
`;

const TestimonialText = styled.p`
  font-size: 1rem;
  color: #e2e8f0;
  margin: 0 0 24px 0;
  line-height: 1.6;
  font-style: italic;
`;

const TestimonialAuthor = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const AuthorAvatar = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #06b6d4, #10b981);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1.1rem;
`;

const AuthorInfo = styled.div`
  flex: 1;
`;

const AuthorName = styled.div`
  font-size: 1rem;
  font-weight: 600;
  color: white;
  margin-bottom: 4px;
`;

const AuthorTitle = styled.div`
  font-size: 0.875rem;
  color: #94a3b8;
`;

const Rating = styled.div`
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
`;

const StarIcon = styled.div`
  color: ${props => props.filled ? '#fbbf24' : '#374151'};
`;

const CaseStudiesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 32px;
  margin-bottom: 60px;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 24px;
  }
`;

const CaseStudyCard = styled(motion.div)`
  padding: 32px 24px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  backdrop-filter: blur(10px);
`;

const CaseStudyHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
`;

const CaseStudyIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #06b6d4, #10b981);
  color: white;
`;

const CaseStudyTitle = styled.h4`
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  color: white;
`;

const CaseStudyDescription = styled.p`
  font-size: 1rem;
  color: #94a3b8;
  margin: 0 0 20px 0;
  line-height: 1.6;
`;

const CaseStudyResults = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const Result = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  color: #10b981;
`;

const ResultIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
`;

const CTA = styled(motion.div)`
  text-align: center;
  padding: 40px 32px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  backdrop-filter: blur(10px);
`;

const CTATitle = styled.h3`
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: white;
`;

const CTADescription = styled.p`
  font-size: 1rem;
  color: #94a3b8;
  margin: 0 0 24px 0;
`;

const CTAButton = styled(motion.button)`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #06b6d4 0%, #10b981 100%);
  border: none;
  border-radius: 12px;
  padding: 16px 32px;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 20px 40px rgba(6, 182, 212, 0.3);
  }
`;

const SocialProofSection = () => {
  const stats = [
    {
      icon: Users,
      number: "10,000+",
      label: "Активных пользователей"
    },
    {
      icon: TrendingUp,
      number: "1M+",
      label: "Постов создано"
    },
    {
      icon: Star,
      number: "4.9",
      label: "Рейтинг пользователей"
    },
    {
      icon: Award,
      number: "99.9%",
      label: "Время работы"
    }
  ];

  const testimonials = [
    {
      text: "AI Content Orchestrator изменил наш подход к контент-маркетингу. Теперь мы создаем в 10 раз больше контента с лучшим качеством.",
      author: {
        name: "Анна Петрова",
        title: "CMO, TechStart",
        avatar: "АП"
      },
      rating: 5
    },
    {
      text: "Отличный инструмент для автоматизации SMM. Экономит массу времени и позволяет сосредоточиться на стратегии, а не на рутине.",
      author: {
        name: "Дмитрий Козлов",
        title: "SMM-менеджер, Digital Agency",
        avatar: "ДК"
      },
      rating: 5
    },
    {
      text: "Простота использования и мощные возможности AI. Наша команда быстро освоила платформу и уже видит результаты.",
      author: {
        name: "Елена Смирнова",
        title: "Руководитель маркетинга, E-commerce",
        avatar: "ЕС"
      },
      rating: 5
    }
  ];

  const caseStudies = [
    {
      icon: TrendingUp,
      title: "E-commerce компания",
      description: "Увеличила объем контента в 5 раз и рост продаж на 40% за 3 месяца",
      results: [
        "5x увеличение объемов контента",
        "40% рост продаж",
        "60% экономия времени команды",
        "3x рост вовлеченности"
      ]
    },
    {
      icon: Users,
      title: "Digital агентство",
      description: "Автоматизировала контент для 50+ клиентов и увеличила прибыль на 200%",
      results: [
        "50+ клиентов на платформе",
        "200% рост прибыли",
        "95% экономия времени",
        "4.9/5 рейтинг клиентов"
      ]
    }
  ];

  return (
    <Section>
      <SectionHeader>
        <SectionTitle>
          Доверяют тысячи компаний
        </SectionTitle>
        <SectionSubtitle>
          Присоединяйтесь к растущему сообществу успешных маркетологов
        </SectionSubtitle>
      </SectionHeader>

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

      <TestimonialsGrid>
        {testimonials.map((testimonial, index) => (
          <TestimonialCard
            key={index}
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.2 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.02 }}
          >
            <QuoteIcon>
              <Quote size={24} />
            </QuoteIcon>
            
            <Rating>
              {[...Array(5)].map((_, i) => (
                <StarIcon key={i} filled={i < testimonial.rating}>
                  <Star size={16} />
                </StarIcon>
              ))}
            </Rating>
            
            <TestimonialText>"{testimonial.text}"</TestimonialText>
            
            <TestimonialAuthor>
              <AuthorAvatar>{testimonial.author.avatar}</AuthorAvatar>
              <AuthorInfo>
                <AuthorName>{testimonial.author.name}</AuthorName>
                <AuthorTitle>{testimonial.author.title}</AuthorTitle>
              </AuthorInfo>
            </TestimonialAuthor>
          </TestimonialCard>
        ))}
      </TestimonialsGrid>

      <CaseStudiesGrid>
        {caseStudies.map((caseStudy, index) => (
          <CaseStudyCard
            key={index}
            initial={{ opacity: 0, x: index % 2 === 0 ? -50 : 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.2 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.02 }}
          >
            <CaseStudyHeader>
              <CaseStudyIcon>
                <caseStudy.icon size={28} />
              </CaseStudyIcon>
              <CaseStudyTitle>{caseStudy.title}</CaseStudyTitle>
            </CaseStudyHeader>
            
            <CaseStudyDescription>{caseStudy.description}</CaseStudyDescription>
            
            <CaseStudyResults>
              {caseStudy.results.map((result, resultIndex) => (
                <Result key={resultIndex}>
                  <ResultIcon>
                    <CheckCircle size={12} />
                  </ResultIcon>
                  {result}
                </Result>
              ))}
            </CaseStudyResults>
          </CaseStudyCard>
        ))}
      </CaseStudiesGrid>

      <CTA
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        viewport={{ once: true }}
      >
        <CTATitle>Готовы присоединиться?</CTATitle>
        <CTADescription>
          Начните создавать контент с AI уже сегодня
        </CTADescription>
        <CTAButton
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          Начать бесплатно
          <ArrowRight size={20} />
        </CTAButton>
      </CTA>
    </Section>
  );
};

export default SocialProofSection;
