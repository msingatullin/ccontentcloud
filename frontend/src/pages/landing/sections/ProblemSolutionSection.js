import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { 
  Clock, 
  Users, 
  AlertTriangle, 
  CheckCircle, 
  Zap, 
  Target,
  TrendingUp,
  Shield
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

const ComparisonContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  margin-bottom: 80px;
  
  @media (max-width: 968px) {
    grid-template-columns: 1fr;
    gap: 40px;
  }
`;

const ProblemColumn = styled.div`
  position: relative;
`;

const SolutionColumn = styled.div`
  position: relative;
`;

const ColumnHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
  padding: 16px 24px;
  border-radius: 16px;
  background: ${props => props.isProblem 
    ? 'rgba(239, 68, 68, 0.1)' 
    : 'rgba(16, 185, 129, 0.1)'
  };
  border: 1px solid ${props => props.isProblem 
    ? 'rgba(239, 68, 68, 0.3)' 
    : 'rgba(16, 185, 129, 0.3)'
  };
`;

const ColumnIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: ${props => props.isProblem 
    ? 'rgba(239, 68, 68, 0.2)' 
    : 'rgba(16, 185, 129, 0.2)'
  };
  color: ${props => props.isProblem ? '#ef4444' : '#10b981'};
`;

const ColumnTitle = styled.h3`
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: ${props => props.isProblem ? '#ef4444' : '#10b981'};
`;

const ProblemList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const SolutionList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const ProblemItem = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.1);
  border-radius: 12px;
`;

const SolutionItem = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.1);
  border-radius: 12px;
`;

const ItemIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: ${props => props.isProblem 
    ? 'rgba(239, 68, 68, 0.1)' 
    : 'rgba(16, 185, 129, 0.1)'
  };
  color: ${props => props.isProblem ? '#ef4444' : '#10b981'};
  flex-shrink: 0;
`;

const ItemContent = styled.div`
  flex: 1;
`;

const ItemTitle = styled.h4`
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: white;
`;

const ItemDescription = styled.p`
  font-size: 0.95rem;
  color: #94a3b8;
  margin: 0;
  line-height: 1.5;
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

const ProblemSolutionSection = () => {
  const problems = [
    {
      icon: Clock,
      title: "Тратите часы на создание контента",
      description: "Каждый пост требует времени на написание, оформление и адаптацию под разные платформы"
    },
    {
      icon: Users,
      title: "Нет времени на стратегию",
      description: "Фокус на создании контента не оставляет времени на анализ аудитории и планирование"
    },
    {
      icon: AlertTriangle,
      title: "Низкое качество из-за спешки",
      description: "Постоянная нехватка времени приводит к снижению качества и вовлеченности"
    },
    {
      icon: Target,
      title: "Сложно масштабировать",
      description: "Ручная работа не позволяет увеличить объемы контента без пропорционального роста команды"
    }
  ];

  const solutions = [
    {
      icon: Zap,
      title: "Автоматическое создание контента",
      description: "AI-агенты создают качественный контент за минуты, адаптируя его под каждую платформу"
    },
    {
      icon: TrendingUp,
      title: "Стратегический подход",
      description: "Анализ трендов и аудитории помогает создавать контент, который действительно работает"
    },
    {
      icon: CheckCircle,
      title: "Высокое качество",
      description: "AI проверяет факты, оптимизирует под SEO и адаптирует под специфику каждой платформы"
    },
    {
      icon: Shield,
      title: "Легкое масштабирование",
      description: "От 1 до 1000 постов в месяц - система автоматически адаптируется под ваши потребности"
    }
  ];

  const stats = [
    {
      icon: Clock,
      number: "95%",
      label: "Экономия времени"
    },
    {
      icon: TrendingUp,
      number: "3x",
      label: "Рост вовлеченности"
    },
    {
      icon: Target,
      number: "10x",
      label: "Увеличение объемов"
    },
    {
      icon: CheckCircle,
      number: "99%",
      label: "Точность публикаций"
    }
  ];

  return (
    <Section>
      <SectionHeader>
        <SectionTitle>
          От хаоса к системе
        </SectionTitle>
        <SectionSubtitle>
          Посмотрите, как AI Content Orchestrator решает главные проблемы контент-маркетинга
        </SectionSubtitle>
      </SectionHeader>

      <ComparisonContainer>
        <ProblemColumn>
          <ColumnHeader isProblem={true}>
            <ColumnIcon isProblem={true}>
              <AlertTriangle size={24} />
            </ColumnIcon>
            <ColumnTitle isProblem={true}>Без AI Orchestrator</ColumnTitle>
          </ColumnHeader>
          <ProblemList>
            {problems.map((problem, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -30 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <ProblemItem>
                  <ItemIcon isProblem={true}>
                    <problem.icon size={20} />
                  </ItemIcon>
                  <ItemContent>
                    <ItemTitle>{problem.title}</ItemTitle>
                    <ItemDescription>{problem.description}</ItemDescription>
                  </ItemContent>
                </ProblemItem>
              </motion.div>
            ))}
          </ProblemList>
        </ProblemColumn>

        <SolutionColumn>
          <ColumnHeader isProblem={false}>
            <ColumnIcon isProblem={false}>
              <CheckCircle size={24} />
            </ColumnIcon>
            <ColumnTitle isProblem={false}>С AI Orchestrator</ColumnTitle>
          </ColumnHeader>
          <SolutionList>
            {solutions.map((solution, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <SolutionItem>
                  <ItemIcon isProblem={false}>
                    <solution.icon size={20} />
                  </ItemIcon>
                  <ItemContent>
                    <ItemTitle>{solution.title}</ItemTitle>
                    <ItemDescription>{solution.description}</ItemDescription>
                  </ItemContent>
                </SolutionItem>
              </motion.div>
            ))}
          </SolutionList>
        </SolutionColumn>
      </ComparisonContainer>

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
    </Section>
  );
};

export default ProblemSolutionSection;
