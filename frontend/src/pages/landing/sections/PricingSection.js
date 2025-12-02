import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { 
  Check, 
  X, 
  Star, 
  ArrowRight,
  Zap,
  Crown,
  Building
} from 'lucide-react';
import { useQuery } from 'react-query';
import api from '../../../services/api';
import toast from 'react-hot-toast';

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

const BillingToggle = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 60px;
`;

const ToggleLabel = styled.span`
  font-size: 1rem;
  color: ${props => props.active ? '#06b6d4' : '#94a3b8'};
  font-weight: 500;
`;

const Toggle = styled.div`
  position: relative;
  width: 60px;
  height: 32px;
  background: ${props => props.active ? '#06b6d4' : 'rgba(255, 255, 255, 0.1)'};
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
`;

const ToggleSlider = styled.div`
  position: absolute;
  top: 4px;
  left: ${props => props.active ? '32px' : '4px'};
  width: 24px;
  height: 24px;
  background: white;
  border-radius: 50%;
  transition: all 0.3s ease;
`;

const PlansGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
  margin-bottom: 60px;
  
  @media (max-width: 968px) {
    grid-template-columns: 1fr;
    gap: 24px;
  }
`;

const PlanCard = styled(motion.div)`
  position: relative;
  padding: 40px 32px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid ${props => props.popular ? 'rgba(6, 182, 212, 0.3)' : 'rgba(255, 255, 255, 0.1)'};
  border-radius: 24px;
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
    background: ${props => props.popular 
      ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(16, 185, 129, 0.1))'
      : 'transparent'
    };
    opacity: ${props => props.popular ? 1 : 0};
    transition: opacity 0.3s ease;
    z-index: -1;
  }
  
  &:hover::before {
    opacity: 1;
  }
`;

const PopularBadge = styled.div`
  position: absolute;
  top: -1px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #06b6d4, #10b981);
  color: white;
  padding: 8px 24px;
  border-radius: 0 0 12px 12px;
  font-size: 0.875rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
`;

const PlanIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: ${props => {
    switch (props.planType) {
      case 'free': return 'rgba(255, 255, 255, 0.1)';
      case 'pro': return 'linear-gradient(135deg, #06b6d4, #10b981)';
      case 'enterprise': return 'linear-gradient(135deg, #8b5cf6, #a855f7)';
      default: return 'rgba(255, 255, 255, 0.1)';
    }
  }};
  color: white;
  margin: 0 auto 24px;
`;

const PlanName = styled.h3`
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: white;
`;

const PlanDescription = styled.p`
  font-size: 1rem;
  color: #94a3b8;
  margin: 0 0 24px 0;
  line-height: 1.5;
`;

const PlanPrice = styled.div`
  margin-bottom: 32px;
`;

const PriceAmount = styled.div`
  font-size: 3rem;
  font-weight: 700;
  color: #06b6d4;
  margin-bottom: 4px;
`;

const PricePeriod = styled.div`
  font-size: 1rem;
  color: #94a3b8;
`;

const PlanFeatures = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 32px;
  text-align: left;
`;

const Feature = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.95rem;
  color: ${props => props.included ? '#10b981' : '#64748b'};
`;

const FeatureIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: ${props => props.included 
    ? 'rgba(16, 185, 129, 0.2)' 
    : 'rgba(100, 116, 139, 0.2)'
  };
  color: ${props => props.included ? '#10b981' : '#64748b'};
  flex-shrink: 0;
`;

const PlanButton = styled(motion.button)`
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: ${props => {
    switch (props.planType) {
      case 'free': return 'transparent';
      case 'pro': return 'linear-gradient(135deg, #06b6d4, #10b981)';
      case 'enterprise': return 'linear-gradient(135deg, #8b5cf6, #a855f7)';
      default: return 'transparent';
    }
  }};
  border: ${props => props.planType === 'free' 
    ? '2px solid rgba(255, 255, 255, 0.2)' 
    : 'none'
  };
  border-radius: 12px;
  padding: 16px 32px;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: ${props => props.planType === 'free' 
      ? '0 10px 20px rgba(255, 255, 255, 0.1)'
      : '0 20px 40px rgba(6, 182, 212, 0.3)'
    };
  }
`;

const LoadingSpinner = styled.div`
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const PricingSection = () => {
  const [isYearly, setIsYearly] = useState(false);
  const [loadingPlan, setLoadingPlan] = useState(null);

  // Загрузка тарифных планов
  const { data: plans, isLoading, error } = useQuery(
    'billing-plans',
    () => api.get('/api/v1/billing/plans').then(res => res.data),
    {
      staleTime: 5 * 60 * 1000, // 5 минут
      cacheTime: 10 * 60 * 1000, // 10 минут
    }
  );

  const handleSubscribe = async (planId) => {
    setLoadingPlan(planId);
    try {
      const response = await api.post('/api/v1/billing/subscription', {
        plan_id: planId,
        billing_period: isYearly ? 'yearly' : 'monthly'
      });
      
      if (response.data.payment_url) {
        window.open(response.data.payment_url, '_blank');
        toast.success('Перенаправление на страницу оплаты...');
      } else {
        toast.success('Подписка активирована!');
      }
    } catch (error) {
      console.error('Ошибка создания подписки:', error);
      toast.error('Ошибка при создании подписки. Попробуйте позже.');
    } finally {
      setLoadingPlan(null);
    }
  };

  // Fallback планы если API недоступен
  const fallbackPlans = [
    {
      id: 'free',
      name: 'Free',
      description: 'Базовый план для начала работы',
      price_monthly: 0,
      price_yearly: 0,
      features: [
        { name: '50 постов в месяц', included: true },
        { name: '3 AI-агента', included: true },
        { name: 'Telegram, VK', included: true },
        { name: '100 API вызовов/день', included: true },
        { name: '1 GB хранилища', included: true },
        { name: 'Сообщество поддержка', included: true },
        { name: 'Аналитика', included: false },
        { name: 'Приоритетная поддержка', included: false }
      ],
      plan_type: 'free',
      is_popular: false
    },
    {
      id: 'pro',
      name: 'Pro',
      description: 'Для профессионалов и малого бизнеса',
      price_monthly: 299000, // в копейках
      price_yearly: 2990000,
      features: [
        { name: 'Неограниченные посты', included: true },
        { name: 'Все 10 AI-агентов', included: true },
        { name: 'Все платформы', included: true },
        { name: '10,000 API вызовов/день', included: true },
        { name: '100 GB хранилища', included: true },
        { name: 'Приоритетная поддержка', included: true },
        { name: 'Детальная аналитика', included: true },
        { name: 'A/B тестирование', included: true }
      ],
      plan_type: 'pro',
      is_popular: true
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      description: 'Для крупных компаний и команд',
      price_monthly: 0,
      price_yearly: 0,
      features: [
        { name: 'Неограниченные посты', included: true },
        { name: 'Все AI-агенты', included: true },
        { name: 'Все платформы', included: true },
        { name: 'Неограниченные API вызовы', included: true },
        { name: 'Неограниченное хранилище', included: true },
        { name: 'Персональный менеджер', included: true },
        { name: 'White-label решение', included: true },
        { name: 'API доступ', included: true }
      ],
      plan_type: 'enterprise',
      is_popular: false
    }
  ];

  const displayPlans = plans?.plans || fallbackPlans;

  const formatPrice = (priceInKopecks) => {
    if (priceInKopecks === 0) return 'Бесплатно';
    const rubles = priceInKopecks / 100;
    return `${rubles.toLocaleString('ru-RU')} ₽`;
  };

  const getPlanIcon = (planType) => {
    switch (planType) {
      case 'free': return Zap;
      case 'pro': return Star;
      case 'enterprise': return Building;
      default: return Zap;
    }
  };

  const getButtonText = (planType) => {
    switch (planType) {
      case 'free': return 'Начать бесплатно';
      case 'pro': return 'Выбрать Pro';
      case 'enterprise': return 'Связаться с нами';
      default: return 'Выбрать план';
    }
  };

  return (
    <Section>
      <SectionHeader>
        <SectionTitle>
          Выберите свой план
        </SectionTitle>
        <SectionSubtitle>
          Гибкие тарифы для любого масштаба бизнеса
        </SectionSubtitle>
      </SectionHeader>

      <BillingToggle>
        <ToggleLabel active={!isYearly}>Ежемесячно</ToggleLabel>
        <Toggle 
          active={isYearly} 
          onClick={() => setIsYearly(!isYearly)}
        >
          <ToggleSlider active={isYearly} />
        </Toggle>
        <ToggleLabel active={isYearly}>
          Ежегодно 
          <span style={{ color: '#10b981', marginLeft: '4px' }}>(-20%)</span>
        </ToggleLabel>
      </BillingToggle>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <LoadingSpinner />
        </div>
      ) : (
        <PlansGrid>
          {displayPlans.map((plan, index) => {
            const IconComponent = getPlanIcon(plan.plan_type);
            const price = isYearly ? plan.price_yearly : plan.price_monthly;
            
            return (
              <PlanCard
                key={plan.id}
                popular={plan.is_popular}
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.2 }}
                viewport={{ once: true }}
                whileHover={{ scale: 1.02 }}
              >
                {plan.is_popular && (
                  <PopularBadge>
                    <Star size={16} />
                    Популярный
                  </PopularBadge>
                )}
                
                <PlanIcon planType={plan.plan_type}>
                  <IconComponent size={40} />
                </PlanIcon>
                
                <PlanName>{plan.name}</PlanName>
                <PlanDescription>{plan.description}</PlanDescription>
                
                <PlanPrice>
                  <PriceAmount>
                    {formatPrice(price)}
                  </PriceAmount>
                  <PricePeriod>
                    {price === 0 ? '' : `за ${isYearly ? 'год' : 'месяц'}`}
                  </PricePeriod>
                </PlanPrice>
                
                <PlanFeatures>
                  {plan.features.map((feature, featureIndex) => {
                    // Поддержка как строк так и объектов {name, included}
                    const featureName = typeof feature === 'string' ? feature : feature.name;
                    const featureIncluded = typeof feature === 'string' ? true : feature.included;
                    
                    return (
                      <Feature key={featureIndex} included={featureIncluded}>
                        <FeatureIcon included={featureIncluded}>
                          {featureIncluded ? <Check size={12} /> : <X size={12} />}
                        </FeatureIcon>
                        {featureName}
                      </Feature>
                    );
                  })}
                </PlanFeatures>
                
                <PlanButton
                  planType={plan.plan_type}
                  onClick={() => handleSubscribe(plan.id)}
                  disabled={loadingPlan === plan.id}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {loadingPlan === plan.id ? (
                    <LoadingSpinner />
                  ) : (
                    <>
                      {getButtonText(plan.plan_type)}
                      <ArrowRight size={20} />
                    </>
                  )}
                </PlanButton>
              </PlanCard>
            );
          })}
        </PlansGrid>
      )}

      {error && (
        <div style={{ 
          textAlign: 'center', 
          padding: '20px', 
          color: '#ef4444',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '12px',
          margin: '20px 0'
        }}>
          Ошибка загрузки тарифов. Используются демо-планы.
        </div>
      )}
    </Section>
  );
};

export default PricingSection;
