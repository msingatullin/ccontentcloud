import React from 'react';
import { Helmet } from 'react-helmet-async';
import styled from 'styled-components';
import { motion } from 'framer-motion';

// Импорт секций
import HeroSection from './sections/HeroSection';
import ProblemSolutionSection from './sections/ProblemSolutionSection';
import HowItWorksSection from './sections/HowItWorksSection';
import PlatformsSection from './sections/PlatformsSection';
import BenefitsSection from './sections/BenefitsSection';
import DemoSection from './sections/DemoSection';
import PricingSection from './sections/PricingSection';
import SocialProofSection from './sections/SocialProofSection';
import FinalCTASection from './sections/FinalCTASection';

// Импорт компонентов
import LandingNavbar from './components/LandingNavbar';
import Footer from './components/Footer';

const LandingContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: #ffffff;
  overflow-x: hidden;
`;

const Section = styled(motion.section)`
  padding: 80px 0;
  
  @media (max-width: 768px) {
    padding: 60px 0;
  }
`;

const LandingPage = () => {
  const sectionVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.8, ease: "easeOut" }
    }
  };

  return (
    <>
      <Helmet>
        <title>AI Content Orchestrator - Автоматизация контент-маркетинга</title>
        <meta 
          name="description" 
          content="Создавайте, адаптируйте и публикуйте контент на всех платформах автоматически. 10 AI-агентов для полной автоматизации контент-маркетинга." 
        />
        <meta 
          name="keywords" 
          content="AI, контент-маркетинг, автоматизация, социальные сети, блог, SMM, контент-план" 
        />
        <meta property="og:title" content="AI Content Orchestrator - Автоматизация контент-маркетинга" />
        <meta 
          property="og:description" 
          content="Создавайте, адаптируйте и публикуйте контент на всех платформах автоматически. 10 AI-агентов для полной автоматизации контент-маркетинга." 
        />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://content-curator-1046574462613.us-central1.run.app" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="AI Content Orchestrator - Автоматизация контент-маркетинга" />
        <meta 
          name="twitter:description" 
          content="Создавайте, адаптируйте и публикуйте контент на всех платформах автоматически. 10 AI-агентов для полной автоматизации контент-маркетинга." 
        />
        <link rel="canonical" href="https://content-curator-1046574462613.us-central1.run.app" />
      </Helmet>

      <LandingContainer>
        <LandingNavbar />
        
        <HeroSection />
        
        <Section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
        >
          <ProblemSolutionSection />
        </Section>
        
        <Section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
        >
          <HowItWorksSection />
        </Section>
        
        <Section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
        >
          <PlatformsSection />
        </Section>
        
        <Section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
        >
          <BenefitsSection />
        </Section>
        
        <Section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
        >
          <DemoSection />
        </Section>
        
        <Section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
        >
          <PricingSection />
        </Section>
        
        <Section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
        >
          <SocialProofSection />
        </Section>
        
        <Section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
        >
          <FinalCTASection />
        </Section>
        
        <Footer />
      </LandingContainer>
    </>
  );
};

export default LandingPage;
