import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { 
  MessageCircle, 
  Instagram, 
  Youtube, 
  Facebook, 
  Twitter,
  Linkedin,
  Globe,
  Smartphone,
  Monitor,
  Tablet
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

const PlatformsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 32px;
  margin-bottom: 80px;
`;

const PlatformCard = styled(motion.div)`
  position: relative;
  padding: 32px 24px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  backdrop-filter: blur(10px);
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
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: -1;
  }
  
  &:hover::before {
    opacity: 1;
  }
`;

const PlatformIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: ${props => props.color || 'linear-gradient(135deg, #06b6d4, #10b981)'};
  color: white;
  margin: 0 auto 24px;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    top: -4px;
    left: -4px;
    right: -4px;
    bottom: -4px;
    background: ${props => props.color || 'linear-gradient(135deg, #06b6d4, #10b981)'};
    border-radius: 24px;
    opacity: 0.3;
    z-index: -1;
  }
`;

const PlatformName = styled.h3`
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: white;
`;

const PlatformDescription = styled.p`
  font-size: 1rem;
  color: #94a3b8;
  margin: 0 0 24px 0;
  line-height: 1.6;
`;

const PlatformFeatures = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
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
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
    font-size: 0.8rem;
    font-weight: 600;
  }
`;

const FormatsSection = styled.div`
  margin-top: 80px;
`;

const FormatsTitle = styled.h3`
  font-size: 2rem;
  font-weight: 600;
  text-align: center;
  margin: 0 0 40px 0;
  color: white;
`;

const FormatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
`;

const FormatCard = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
`;

const FormatIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(6, 182, 212, 0.1);
  color: #06b6d4;
  flex-shrink: 0;
`;

const FormatContent = styled.div`
  flex: 1;
`;

const FormatName = styled.div`
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
  margin-bottom: 4px;
`;

const FormatDescription = styled.div`
  font-size: 0.9rem;
  color: #94a3b8;
`;

const PlatformsSection = () => {
  const platforms = [
    {
      name: "Telegram",
      icon: MessageCircle,
      color: "linear-gradient(135deg, #0088cc, #229ED9)",
      description: "Каналы, группы, боты - полная автоматизация",
      features: [
        "Посты в каналы",
        "Stories и медиа",
        "Интерактивные кнопки",
        "Автоматические рассылки"
      ]
    },
    {
      name: "Instagram",
      icon: Instagram,
      color: "linear-gradient(135deg, #E4405F, #F77737)",
      description: "Посты, Stories, Reels - все форматы",
      features: [
        "Посты с хештегами",
        "Stories с музыкой",
        "Reels и IGTV",
        "Автоматические комментарии"
      ]
    },
    {
      name: "YouTube",
      icon: Youtube,
      color: "linear-gradient(135deg, #FF0000, #FF4444)",
      description: "Видео, Shorts, описания - полный цикл",
      features: [
        "Описания видео",
        "Thumbnails",
        "YouTube Shorts",
        "SEO оптимизация"
      ]
    },
    {
      name: "VK",
      icon: Facebook,
      color: "linear-gradient(135deg, #0077FF, #4A90E2)",
      description: "ВКонтакте - посты, Stories, реклама",
      features: [
        "Посты в группы",
        "VK Stories",
        "Рекламные креативы",
        "Таргетинг"
      ]
    },
    {
      name: "Facebook",
      icon: Facebook,
      color: "linear-gradient(135deg, #1877F2, #42A5F5)",
      description: "Facebook и Meta платформы",
      features: [
        "Посты в группы",
        "Facebook Stories",
        "Рекламные креативы",
        "Аналитика"
      ]
    },
    {
      name: "LinkedIn",
      icon: Linkedin,
      color: "linear-gradient(135deg, #0077B5, #00A0DC)",
      description: "Профессиональный контент",
      features: [
        "Статьи и посты",
        "LinkedIn Stories",
        "Профессиональные темы",
        "B2B контент"
      ]
    }
  ];

  const formats = [
    {
      icon: MessageCircle,
      name: "Текстовые посты",
      description: "Адаптированные под каждую платформу"
    },
    {
      icon: Smartphone,
      name: "Stories",
      description: "Временный контент с анимацией"
    },
    {
      icon: Monitor,
      name: "Длинные статьи",
      description: "Подробные материалы для блогов"
    },
    {
      icon: Globe,
      name: "SEO контент",
      description: "Оптимизированный для поиска"
    },
    {
      icon: Tablet,
      name: "Карусели",
      description: "Многостраничные посты"
    },
    {
      icon: Youtube,
      name: "Видео контент",
      description: "Скрипты и описания"
    }
  ];

  return (
    <Section>
      <SectionHeader>
        <SectionTitle>
          Все платформы в одном месте
        </SectionTitle>
        <SectionSubtitle>
          Создавайте контент для всех популярных платформ автоматически
        </SectionSubtitle>
      </SectionHeader>

      <PlatformsGrid>
        {platforms.map((platform, index) => (
          <PlatformCard
            key={index}
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.05 }}
          >
            <PlatformIcon color={platform.color}>
              <platform.icon size={40} />
            </PlatformIcon>
            <PlatformName>{platform.name}</PlatformName>
            <PlatformDescription>{platform.description}</PlatformDescription>
            <PlatformFeatures>
              {platform.features.map((feature, featureIndex) => (
                <Feature key={featureIndex}>{feature}</Feature>
              ))}
            </PlatformFeatures>
          </PlatformCard>
        ))}
      </PlatformsGrid>

      <FormatsSection>
        <FormatsTitle>Поддерживаемые форматы</FormatsTitle>
        <FormatsGrid>
          {formats.map((format, index) => (
            <FormatCard
              key={index}
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.02 }}
            >
              <FormatIcon>
                <format.icon size={24} />
              </FormatIcon>
              <FormatContent>
                <FormatName>{format.name}</FormatName>
                <FormatDescription>{format.description}</FormatDescription>
              </FormatContent>
            </FormatCard>
          ))}
        </FormatsGrid>
      </FormatsSection>
    </Section>
  );
};

export default PlatformsSection;
