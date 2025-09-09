import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { 
  Mail, 
  Phone, 
  MapPin,
  Twitter,
  Linkedin,
  Github,
  ArrowRight
} from 'lucide-react';

const FooterContainer = styled.footer`
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 60px 0 20px;
`;

const FooterContent = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
`;

const FooterTop = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 40px;
  margin-bottom: 40px;
  
  @media (max-width: 968px) {
    grid-template-columns: 1fr 1fr;
    gap: 32px;
  }
  
  @media (max-width: 480px) {
    grid-template-columns: 1fr;
    gap: 24px;
  }
`;

const FooterColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
`;

const LogoIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #06b6d4, #10b981);
  color: white;
`;

const LogoText = styled.div`
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
`;

const FooterDescription = styled.p`
  font-size: 1rem;
  color: #94a3b8;
  line-height: 1.6;
  margin: 0;
`;

const ColumnTitle = styled.h4`
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
  margin: 0 0 16px 0;
`;

const FooterLinks = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const FooterLink = styled.a`
  font-size: 0.95rem;
  color: #94a3b8;
  text-decoration: none;
  transition: color 0.3s ease;
  
  &:hover {
    color: #06b6d4;
  }
`;

const ContactInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const ContactItem = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.95rem;
  color: #94a3b8;
`;

const ContactIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(6, 182, 212, 0.1);
  color: #06b6d4;
  flex-shrink: 0;
`;

const SocialLinks = styled.div`
  display: flex;
  gap: 12px;
`;

const SocialLink = styled(motion.a)`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  text-decoration: none;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(6, 182, 212, 0.1);
    border-color: rgba(6, 182, 212, 0.3);
    color: #06b6d4;
  }
`;

const Newsletter = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
`;

const NewsletterTitle = styled.h4`
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
  margin: 0 0 8px 0;
`;

const NewsletterDescription = styled.p`
  font-size: 0.9rem;
  color: #94a3b8;
  margin: 0 0 16px 0;
`;

const NewsletterForm = styled.form`
  display: flex;
  gap: 8px;
  
  @media (max-width: 480px) {
    flex-direction: column;
  }
`;

const NewsletterInput = styled.input`
  flex: 1;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  font-size: 0.9rem;
  color: white;
  
  &::placeholder {
    color: #94a3b8;
  }
  
  &:focus {
    outline: none;
    border-color: #06b6d4;
  }
`;

const NewsletterButton = styled(motion.button)`
  display: flex;
  align-items: center;
  gap: 4px;
  background: linear-gradient(135deg, #06b6d4, #10b981);
  border: none;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 0.9rem;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-1px);
  }
`;

const FooterBottom = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
`;

const Copyright = styled.div`
  font-size: 0.9rem;
  color: #64748b;
`;

const FooterBottomLinks = styled.div`
  display: flex;
  gap: 24px;
  
  @media (max-width: 480px) {
    flex-direction: column;
    gap: 12px;
  }
`;

const FooterBottomLink = styled.a`
  font-size: 0.9rem;
  color: #64748b;
  text-decoration: none;
  transition: color 0.3s ease;
  
  &:hover {
    color: #06b6d4;
  }
`;

const Footer = () => {
  const handleNewsletterSubmit = (e) => {
    e.preventDefault();
    // Обработка подписки на рассылку
    console.log('Newsletter subscription');
  };

  return (
    <FooterContainer>
      <FooterContent>
        <FooterTop>
          <FooterColumn>
            <Logo>
              <LogoIcon>
                <ArrowRight size={24} />
              </LogoIcon>
              <LogoText>AI Content Orchestrator</LogoText>
            </Logo>
            <FooterDescription>
              Автоматизируйте создание контента с помощью 10 AI-агентов. 
              Создавайте, адаптируйте и публикуйте контент на всех платформах автоматически.
            </FooterDescription>
            <SocialLinks>
              <SocialLink
                href="#"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <Twitter size={20} />
              </SocialLink>
              <SocialLink
                href="#"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <Linkedin size={20} />
              </SocialLink>
              <SocialLink
                href="#"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <Github size={20} />
              </SocialLink>
            </SocialLinks>
          </FooterColumn>

          <FooterColumn>
            <ColumnTitle>Продукт</ColumnTitle>
            <FooterLinks>
              <FooterLink href="#">Возможности</FooterLink>
              <FooterLink href="#">Тарифы</FooterLink>
              <FooterLink href="#">API</FooterLink>
              <FooterLink href="#">Интеграции</FooterLink>
              <FooterLink href="#">Обновления</FooterLink>
            </FooterLinks>
          </FooterColumn>

          <FooterColumn>
            <ColumnTitle>Компания</ColumnTitle>
            <FooterLinks>
              <FooterLink href="#">О нас</FooterLink>
              <FooterLink href="#">Блог</FooterLink>
              <FooterLink href="#">Карьера</FooterLink>
              <FooterLink href="#">Партнеры</FooterLink>
              <FooterLink href="#">Пресса</FooterLink>
            </FooterLinks>
          </FooterColumn>

          <FooterColumn>
            <ColumnTitle>Поддержка</ColumnTitle>
            <ContactInfo>
              <ContactItem>
                <ContactIcon>
                  <Mail size={16} />
                </ContactIcon>
                support@aicontent.com
              </ContactItem>
              <ContactItem>
                <ContactIcon>
                  <Phone size={16} />
                </ContactIcon>
                +7 (800) 123-45-67
              </ContactItem>
              <ContactItem>
                <ContactIcon>
                  <MapPin size={16} />
                </ContactIcon>
                Москва, Россия
              </ContactItem>
            </ContactInfo>
            
            <Newsletter>
              <NewsletterTitle>Подписка на новости</NewsletterTitle>
              <NewsletterDescription>
                Получайте последние обновления и советы по контент-маркетингу
              </NewsletterDescription>
              <NewsletterForm onSubmit={handleNewsletterSubmit}>
                <NewsletterInput
                  type="email"
                  placeholder="Ваш email"
                  required
                />
                <NewsletterButton
                  type="submit"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  Подписаться
                  <ArrowRight size={16} />
                </NewsletterButton>
              </NewsletterForm>
            </Newsletter>
          </FooterColumn>
        </FooterTop>

        <FooterBottom>
          <Copyright>
            © 2024 AI Content Orchestrator. Все права защищены.
          </Copyright>
          <FooterBottomLinks>
            <FooterBottomLink href="#">Политика конфиденциальности</FooterBottomLink>
            <FooterBottomLink href="#">Условия использования</FooterBottomLink>
            <FooterBottomLink href="#">Cookie</FooterBottomLink>
          </FooterBottomLinks>
        </FooterBottom>
      </FooterContent>
    </FooterContainer>
  );
};

export default Footer;
