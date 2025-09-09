import React, { useState } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, 
  Pause, 
  Monitor, 
  Smartphone, 
  Tablet,
  ArrowRight,
  ArrowLeft,
  Maximize2,
  Eye
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

const DemoContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  align-items: center;
  margin-bottom: 80px;
  
  @media (max-width: 968px) {
    grid-template-columns: 1fr;
    gap: 40px;
  }
`;

const DemoContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 32px;
`;

const DemoTitle = styled.h3`
  font-size: 2rem;
  font-weight: 600;
  margin: 0;
  color: white;
`;

const DemoDescription = styled.p`
  font-size: 1.1rem;
  color: #94a3b8;
  margin: 0;
  line-height: 1.6;
`;

const DemoFeatures = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const Feature = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1rem;
  color: #06b6d4;
`;

const FeatureIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  flex-shrink: 0;
`;

const DemoButtons = styled.div`
  display: flex;
  gap: 16px;
  
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

const DemoVisual = styled.div`
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const DeviceSelector = styled.div`
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  justify-content: center;
`;

const DeviceButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: ${props => props.active ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255, 255, 255, 0.05)'};
  border: 1px solid ${props => props.active ? 'rgba(6, 182, 212, 0.3)' : 'rgba(255, 255, 255, 0.1)'};
  color: ${props => props.active ? '#06b6d4' : '#94a3b8'};
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(6, 182, 212, 0.1);
    border-color: rgba(6, 182, 212, 0.3);
    color: #06b6d4;
  }
`;

const DeviceFrame = styled(motion.div)`
  position: relative;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: ${props => props.device === 'mobile' ? '24px' : '16px'};
  backdrop-filter: blur(10px);
  overflow: hidden;
  width: ${props => {
    switch (props.device) {
      case 'mobile': return '300px';
      case 'tablet': return '400px';
      default: return '500px';
    }
  }};
  height: ${props => {
    switch (props.device) {
      case 'mobile': return '600px';
      case 'tablet': return '500px';
      default: return '400px';
    }
  }};
`;

const DeviceHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
`;

const DeviceTitle = styled.div`
  font-size: 1rem;
  font-weight: 600;
  color: white;
`;

const DeviceControls = styled.div`
  display: flex;
  gap: 8px;
`;

const ControlButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(6, 182, 212, 0.2);
    color: #06b6d4;
  }
`;

const DeviceContent = styled.div`
  padding: 20px;
  height: calc(100% - 80px);
  overflow-y: auto;
`;

const DashboardGrid = styled.div`
  display: grid;
  grid-template-columns: ${props => props.device === 'mobile' ? '1fr' : '1fr 1fr'};
  gap: 16px;
  margin-bottom: 20px;
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

const AgentList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const AgentItem = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
`;

const AgentStatus = styled.div`
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: ${props => props.status === 'active' ? '#10b981' : '#ef4444'};
`;

const AgentName = styled.div`
  font-size: 0.9rem;
  color: white;
  font-weight: 500;
`;

const AgentProgress = styled.div`
  font-size: 0.8rem;
  color: #94a3b8;
  margin-left: auto;
`;

const ScreenshotsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  margin-top: 60px;
`;

const ScreenshotCard = styled(motion.div)`
  position: relative;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  
  &:hover {
    border-color: rgba(6, 182, 212, 0.3);
  }
`;

const ScreenshotImage = styled.div`
  width: 100%;
  height: 200px;
  background: linear-gradient(135deg, #1e293b, #334155);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 0.9rem;
`;

const ScreenshotOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  
  ${ScreenshotCard}:hover & {
    opacity: 1;
  }
`;

const ScreenshotTitle = styled.div`
  padding: 16px;
  font-size: 0.9rem;
  font-weight: 500;
  color: white;
  text-align: center;
`;

const DemoSection = () => {
  const [selectedDevice, setSelectedDevice] = useState('desktop');
  const [isPlaying, setIsPlaying] = useState(false);

  const devices = [
    { id: 'desktop', icon: Monitor, label: 'Desktop' },
    { id: 'tablet', icon: Tablet, label: 'Tablet' },
    { id: 'mobile', icon: Smartphone, label: 'Mobile' }
  ];

  const screenshots = [
    { title: 'Dashboard Overview', description: 'Главная панель управления' },
    { title: 'Content Creation', description: 'Создание контента' },
    { title: 'Analytics', description: 'Аналитика и метрики' },
    { title: 'Settings', description: 'Настройки системы' }
  ];

  return (
    <Section>
      <SectionHeader>
        <SectionTitle>
          Посмотрите в действии
        </SectionTitle>
        <SectionSubtitle>
          Интерактивная демонстрация возможностей AI Content Orchestrator
        </SectionSubtitle>
      </SectionHeader>

      <DemoContainer>
        <DemoContent>
          <DemoTitle>Управляйте всем из одного места</DemoTitle>
          <DemoDescription>
            Современный интерфейс позволяет легко управлять всеми AI-агентами, 
            отслеживать прогресс и анализировать результаты в реальном времени.
          </DemoDescription>
          
          <DemoFeatures>
            <Feature>
              <FeatureIcon>
                <Monitor size={16} />
              </FeatureIcon>
              Адаптивный дизайн для всех устройств
            </Feature>
            <Feature>
              <FeatureIcon>
                <Eye size={16} />
              </FeatureIcon>
              Мониторинг в реальном времени
            </Feature>
            <Feature>
              <FeatureIcon>
                <Maximize2 size={16} />
              </FeatureIcon>
              Детальная аналитика и отчеты
            </Feature>
          </DemoFeatures>

          <DemoButtons>
            <PrimaryButton
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Play size={20} />
              Запустить демо
            </PrimaryButton>
            <SecondaryButton
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Eye size={20} />
              Посмотреть скриншоты
            </SecondaryButton>
          </DemoButtons>
        </DemoContent>

        <DemoVisual>
          <div>
            <DeviceSelector>
              {devices.map((device) => (
                <DeviceButton
                  key={device.id}
                  active={selectedDevice === device.id}
                  onClick={() => setSelectedDevice(device.id)}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <device.icon size={20} />
                </DeviceButton>
              ))}
            </DeviceSelector>

            <DeviceFrame device={selectedDevice}>
              <DeviceHeader>
                <DeviceTitle>AI Content Orchestrator</DeviceTitle>
                <DeviceControls>
                  <ControlButton>
                    <Maximize2 size={16} />
                  </ControlButton>
                  <ControlButton onClick={() => setIsPlaying(!isPlaying)}>
                    {isPlaying ? <Pause size={16} /> : <Play size={16} />}
                  </ControlButton>
                </DeviceControls>
              </DeviceHeader>
              
              <DeviceContent>
                <DashboardGrid device={selectedDevice}>
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
                </DashboardGrid>

                <AgentList>
                  <AgentItem>
                    <AgentStatus status="active" />
                    <AgentName>Chief Content Agent</AgentName>
                    <AgentProgress>100%</AgentProgress>
                  </AgentItem>
                  <AgentItem>
                    <AgentStatus status="active" />
                    <AgentName>Drafting Agent</AgentName>
                    <AgentProgress>85%</AgentProgress>
                  </AgentItem>
                  <AgentItem>
                    <AgentStatus status="active" />
                    <AgentName>Publisher Agent</AgentName>
                    <AgentProgress>60%</AgentProgress>
                  </AgentItem>
                </AgentList>
              </DeviceContent>
            </DeviceFrame>
          </div>
        </DemoVisual>
      </DemoContainer>

      <ScreenshotsGrid>
        {screenshots.map((screenshot, index) => (
          <ScreenshotCard
            key={index}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.05 }}
          >
            <ScreenshotImage>
              {screenshot.title}
            </ScreenshotImage>
            <ScreenshotOverlay>
              <Eye size={32} color="#06b6d4" />
            </ScreenshotOverlay>
            <ScreenshotTitle>{screenshot.title}</ScreenshotTitle>
          </ScreenshotCard>
        ))}
      </ScreenshotsGrid>
    </Section>
  );
};

export default DemoSection;
