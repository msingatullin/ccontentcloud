/**
 * LandingNavbar - Навигация для лендинга
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { Menu, X, Zap } from 'lucide-react';

const NavbarContainer = styled.nav`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  padding: 16px 24px;
  background: ${props => props.$scrolled 
    ? 'rgba(15, 23, 42, 0.95)' 
    : 'transparent'
  };
  backdrop-filter: ${props => props.$scrolled ? 'blur(10px)' : 'none'};
  border-bottom: ${props => props.$scrolled 
    ? '1px solid rgba(255, 255, 255, 0.1)' 
    : 'none'
  };
  transition: all 0.3s ease;
`;

const NavContent = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
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
  font-size: 1.25rem;
  font-weight: 700;
  color: white;
  
  @media (max-width: 768px) {
    display: none;
  }
`;

const NavLinks = styled.div`
  display: flex;
  align-items: center;
  gap: 32px;
  
  @media (max-width: 968px) {
    display: none;
  }
`;

const NavLink = styled.a`
  color: #94a3b8;
  font-size: 0.95rem;
  font-weight: 500;
  text-decoration: none;
  transition: color 0.3s ease;
  cursor: pointer;
  
  &:hover {
    color: #06b6d4;
  }
`;

const NavButtons = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  
  @media (max-width: 968px) {
    display: none;
  }
`;

const LoginButton = styled.button`
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 10px 20px;
  font-size: 0.95rem;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.3);
  }
`;

const SignupButton = styled(motion.button)`
  background: linear-gradient(135deg, #06b6d4, #10b981);
  border: none;
  border-radius: 8px;
  padding: 10px 20px;
  font-size: 0.95rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(6, 182, 212, 0.3);
  }
`;

const MobileMenuButton = styled.button`
  display: none;
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
  
  @media (max-width: 968px) {
    display: flex;
    align-items: center;
    justify-content: center;
  }
`;

const MobileMenu = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.98);
  z-index: 999;
  display: flex;
  flex-direction: column;
  padding: 80px 24px 24px;
`;

const MobileNavLinks = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 40px;
`;

const MobileNavLink = styled.a`
  color: white;
  font-size: 1.25rem;
  font-weight: 500;
  text-decoration: none;
  transition: color 0.3s ease;
  cursor: pointer;
  
  &:hover {
    color: #06b6d4;
  }
`;

const MobileNavButtons = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const CloseButton = styled.button`
  position: absolute;
  top: 24px;
  right: 24px;
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
`;

const LandingNavbar = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (sectionId) => {
    setMobileMenuOpen(false);
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const navLinks = [
    { label: 'Возможности', id: 'features' },
    { label: 'Как это работает', id: 'how-it-works' },
    { label: 'Платформы', id: 'platforms' },
    { label: 'Тарифы', id: 'pricing' },
  ];

  return (
    <>
      <NavbarContainer $scrolled={scrolled}>
        <NavContent>
          <Logo onClick={() => navigate('/')}>
            <LogoIcon>
              <Zap size={24} />
            </LogoIcon>
            <LogoText>AI Content Orchestrator</LogoText>
          </Logo>

          <NavLinks>
            {navLinks.map((link) => (
              <NavLink
                key={link.id}
                onClick={() => scrollToSection(link.id)}
              >
                {link.label}
              </NavLink>
            ))}
          </NavLinks>

          <NavButtons>
            <LoginButton onClick={() => navigate('/login')}>
              Войти
            </LoginButton>
            <SignupButton
              onClick={() => navigate('/register')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Начать бесплатно
            </SignupButton>
          </NavButtons>

          <MobileMenuButton onClick={() => setMobileMenuOpen(true)}>
            <Menu size={24} />
          </MobileMenuButton>
        </NavContent>
      </NavbarContainer>

      {mobileMenuOpen && (
        <MobileMenu
          initial={{ opacity: 0, x: '100%' }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: '100%' }}
          transition={{ duration: 0.3 }}
        >
          <CloseButton onClick={() => setMobileMenuOpen(false)}>
            <X size={24} />
          </CloseButton>

          <MobileNavLinks>
            {navLinks.map((link) => (
              <MobileNavLink
                key={link.id}
                onClick={() => scrollToSection(link.id)}
              >
                {link.label}
              </MobileNavLink>
            ))}
          </MobileNavLinks>

          <MobileNavButtons>
            <LoginButton onClick={() => navigate('/login')}>
              Войти
            </LoginButton>
            <SignupButton onClick={() => navigate('/register')}>
              Начать бесплатно
            </SignupButton>
          </MobileNavButtons>
        </MobileMenu>
      )}
    </>
  );
};

export default LandingNavbar;

