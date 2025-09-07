import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { ArrowRight, Play, Zap, Users, TrendingUp } from 'lucide-react';

const HeroContainer = styled.section`
  min-height: 100vh;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
`;

const AnimatedBackground = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  z-index: 1;
`;

const FloatingElement = styled(motion.div)`
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(45deg, #06b6d4, #10b981);
  opacity: 0.1;
  filter: blur(1px);
`;

const Content = styled.div`
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  align-items: center;
  
  @media (max-width: 968px) {
    grid-template-columns: 1fr;
    gap: 40px;
    text-align: center;
  }
`;

const LeftColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const Badge = styled(motion.div)`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(6, 182, 212, 0.1);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 50px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #06b6d4;
  width: fit-content;
`;

const Title = styled(motion.h1)`
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1.1;
  margin: 0;
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

const Subtitle = styled(motion.p)`
  font-size: 1.25rem;
  line-height: 1.6;
  color: #94a3b8;
  margin: 0;
  max-width: 500px;
  
  @media (max-width: 768px) {
    font-size: 1.1rem;
  }
`;

const Stats = styled(motion.div)`
  display: flex;
  gap: 32px;
  margin-top: 16px;
  
  @media (max-width: 768px) {
    justify-content: center;
    gap: 24px;
  }
  
  @media (max-width: 480px) {
    flex-direction: column;
    gap: 16px;
  }
`;

const Stat = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
`;

const StatNumber = styled.div`
  font-size: 1.5rem;
  font-weight: 700;
  color: #06b6d4;
`;

const StatLabel = styled.div`
  font-size: 0.875rem;
  color: #64748b;
`;

const Buttons = styled(motion.div)`
  display: flex;
  gap: 16px;
  margin-top: 8px;
  
  @media (max-width: 480px) {
    flex-direction: column;
  }
`;

const PrimaryButton = styled(motion.button)`
  display: flex;
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

const SecondaryButton = styled(motion.button)`
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 14px 32px;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: #06b6d4;
    background: rgba(6, 182, 212, 0.1);
  }
`;

const RightColumn = styled.div`
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const DashboardPreview = styled(motion.div)`
  position: relative;
  width: 100%;
  max-width: 500px;
  height: 400px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  overflow: hidden;
`;

const DashboardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
`;

const DashboardTitle = styled.div`
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  color: #10b981;
  font-size: 0.875rem;
`;

const DashboardContent = styled.div`
  padding: 20px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
`;

const MetricCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
`;

const MetricValue = styled.div`
  font-size: 1.5rem;
  font-weight: 700;
  color: #06b6d4;
  margin-bottom: 4px;
`;

const MetricLabel = styled.div`
  font-size: 0.875rem;
  color: #94a3b8;
`;

const HeroSection = () => {
  const floatingElements = Array.from({ length: 20 }, (_, i) => ({
    id: i,
    size: Math.random() * 100 + 50,
    x: Math.random() * 100,
    y: Math.random() * 100,
    delay: Math.random() * 2,
  }));

  return (
    <HeroContainer>
      <AnimatedBackground>
        {floatingElements.map((element) => (
          <FloatingElement
            key={element.id}
            style={{
              width: element.size,
              height: element.size,
              left: `${element.x}%`,
              top: `${element.y}%`,
            }}
            animate={{
              y: [0, -20, 0],
              x: [0, 10, 0],
              scale: [1, 1.1, 1],
            }}
            transition={{
              duration: 4 + Math.random() * 2,
              repeat: Infinity,
              delay: element.delay,
              ease: "easeInOut",
            }}
          />
        ))}
      </AnimatedBackground>

      <Content>
        <LeftColumn>
          <Badge
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Zap size={16} />
            AI-Powered Content Automation
          </Badge>

          <Title
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            Создавайте контент
            <br />
            <span style={{ color: '#06b6d4' }}>автоматически</span>
          </Title>

          <Subtitle
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            10 AI-агентов создают, адаптируют и публикуют контент 
            на всех платформах. От идеи до публикации за минуты.
          </Subtitle>

          <Stats
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Stat>
              <StatNumber>10</StatNumber>
              <StatLabel>AI-агентов</StatLabel>
            </Stat>
            <Stat>
              <StatNumber>8+</StatNumber>
              <StatLabel>Платформ</StatLabel>
            </Stat>
            <Stat>
              <StatNumber>95%</StatNumber>
              <StatLabel>Экономия времени</StatLabel>
            </Stat>
          </Stats>

          <Buttons
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            <PrimaryButton
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Начать бесплатно
              <ArrowRight size={20} />
            </PrimaryButton>
            <SecondaryButton
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Play size={20} />
              Смотреть демо
            </SecondaryButton>
          </Buttons>
        </LeftColumn>

        <RightColumn>
          <DashboardPreview
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.7, duration: 0.8 }}
          >
            <DashboardHeader>
              <DashboardTitle>AI Content Orchestrator</DashboardTitle>
              <StatusIndicator>
                <div style={{ width: 8, height: 8, background: '#10b981', borderRadius: '50%' }} />
                Все агенты активны
              </StatusIndicator>
            </DashboardHeader>
            <DashboardContent>
              <MetricCard>
                <MetricValue>47</MetricValue>
                <MetricLabel>Постов создано</MetricLabel>
              </MetricCard>
              <MetricCard>
                <MetricValue>8</MetricValue>
                <MetricLabel>Платформ</MetricLabel>
              </MetricCard>
              <MetricCard>
                <MetricValue>2.3k</MetricValue>
                <MetricLabel>Просмотров</MetricLabel>
              </MetricCard>
              <MetricCard>
                <MetricValue>156</MetricValue>
                <MetricLabel>Вовлечений</MetricLabel>
              </MetricCard>
            </DashboardContent>
          </DashboardPreview>
        </RightColumn>
      </Content>
    </HeroContainer>
  );
};

export default HeroSection;
