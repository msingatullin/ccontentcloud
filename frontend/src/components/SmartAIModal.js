import React, { useState } from 'react';
import styled from 'styled-components';
import { X, Wand2, Loader2, Link2, Check, ArrowRight, ArrowLeft } from 'lucide-react';
import { toast } from 'react-hot-toast';
import api from '../services/api';

const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
`;

const ModalContent = styled.div`
  background: ${props => props.theme.colors.background};
  padding: 2rem;
  border-radius: ${props => props.theme.borderRadius.lg};
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
`;

const CloseButton = styled.button`
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  cursor: pointer;
  color: ${props => props.theme.colors.textSecondary};
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  
  &:hover {
    background: ${props => props.theme.colors.backgroundTertiary};
    color: ${props => props.theme.colors.text};
  }
`;

const Title = styled.h2`
  font-size: ${props => props.theme.fontSize['2xl']};
  color: ${props => props.theme.colors.text};
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const Subtitle = styled.p`
  color: ${props => props.theme.colors.textSecondary};
  font-size: ${props => props.theme.fontSize.sm};
  margin: 0 0 2rem 0;
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 4px;
  background: ${props => props.theme.colors.backgroundTertiary};
  border-radius: ${props => props.theme.borderRadius.full};
  margin-bottom: 2rem;
  overflow: hidden;
`;

const ProgressFill = styled.div`
  height: 100%;
  background: ${props => props.theme.colors.primary};
  width: ${props => props.progress}%;
  transition: width 0.3s ease;
`;

const QuestionContainer = styled.div`
  margin-bottom: 2rem;
`;

const QuestionTitle = styled.label`
  display: block;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: ${props => props.theme.colors.text};
  font-size: ${props => props.theme.fontSize.base};
`;

const QuestionHelp = styled.p`
  font-size: ${props => props.theme.fontSize.sm};
  color: ${props => props.theme.colors.textSecondary};
  margin: -0.5rem 0 0.75rem 0;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  background: ${props => props.theme.colors.backgroundSecondary};
  color: ${props => props.theme.colors.text};
  font-size: ${props => props.theme.fontSize.base};
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 3px ${props => props.theme.colors.primaryLight};
  }
`;

const TextArea = styled.textarea`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  background: ${props => props.theme.colors.backgroundSecondary};
  color: ${props => props.theme.colors.text};
  font-size: ${props => props.theme.fontSize.base};
  min-height: 100px;
  resize: vertical;
  font-family: inherit;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 3px ${props => props.theme.colors.primaryLight};
  }
`;

const ResourceInputGroup = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
`;

const ResourceInput = styled(Input)`
  flex: 1;
`;

const AnalyzeButton = styled.button`
  padding: 0.75rem 1rem;
  background: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  border-radius: ${props => props.theme.borderRadius.md};
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  white-space: nowrap;
  
  &:hover:not(:disabled) {
    background: ${props => props.theme.colors.primaryHover};
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const OptionGroup = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
`;

const OptionButton = styled.button`
  padding: 0.5rem 1rem;
  border: 2px solid ${props => props.selected ? props.theme.colors.primary : props.theme.colors.border};
  background: ${props => props.selected ? props.theme.colors.primaryLight : props.theme.colors.backgroundSecondary};
  color: ${props => props.selected ? props.theme.colors.primary : props.theme.colors.text};
  border-radius: ${props => props.theme.borderRadius.full};
  cursor: pointer;
  font-size: ${props => props.theme.fontSize.sm};
  font-weight: 500;
  transition: all 0.2s;
  
  &:hover {
    border-color: ${props => props.theme.colors.primary};
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid ${props => props.theme.colors.border};
`;

const Button = styled.button`
  flex: 1;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: ${props => props.theme.borderRadius.md};
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s;
  
  ${props => props.primary ? `
    background: ${props.theme.colors.primary};
    color: white;
    &:hover:not(:disabled) {
      background: ${props.theme.colors.primaryHover};
    }
  ` : `
    background: ${props.theme.colors.backgroundTertiary};
    color: ${props.theme.colors.text};
    &:hover:not(:disabled) {
      background: ${props.theme.colors.backgroundSecondary};
    }
  `}
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const SkipButton = styled.button`
  background: none;
  border: none;
  color: ${props => props.theme.colors.textSecondary};
  cursor: pointer;
  font-size: ${props => props.theme.fontSize.sm};
  padding: 0.5rem;
  margin-top: 0.5rem;
  
  &:hover {
    color: ${props => props.theme.colors.text};
  }
`;

const BUSINESS_GOALS = ['Продажи', 'Охват', 'Вовлечение', 'Лиды', 'Трафик', 'Бренд', 'Лояльность'];
const TONE_OPTIONS = [
  { value: 'professional', label: 'Профессиональный' },
  { value: 'friendly', label: 'Дружелюбный' },
  { value: 'casual', label: 'Неформальный' },
  { value: 'bold', label: 'Смелый' },
  { value: 'formal', label: 'Официальный' },
  { value: 'humorous', label: 'Юмористический' }
];
const PLATFORMS = ['telegram', 'instagram'];

const detectResourceType = (url) => {
  if (!url) return 'website';
  if (url.includes('t.me') || url.includes('telegram')) return 'telegram';
  if (url.includes('instagram.com')) return 'instagram';
  return 'website';
};

export const SmartAIModal = ({ isOpen, onClose, onComplete }) => {
  const [step, setStep] = useState(1);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [resourceUrl, setResourceUrl] = useState('');
  
  const [answers, setAnswers] = useState({
    // Шаг 1: Ниша и продукт
    niche: '',
    product_service: '',
    
    // Шаг 2: Аудитория и боли
    target_audience: '',
    pain_points: [],
    
    // Шаг 3: Стиль и обращение
    tone: 'professional',
    formal_address: 'Вы', // Вы или Ты
    
    // Шаг 4: Цели и платформы
    business_goals: [],
    platforms: ['telegram'],
    
    // Шаг 5: CTA и ключевые слова
    call_to_action: '',
    keywords: []
  });

  const totalSteps = 5;
  const progress = (step / totalSteps) * 100;

  if (!isOpen) return null;

  const handleAnalyzeResource = async () => {
    if (!resourceUrl.trim()) {
      toast.error('Введите URL ресурса');
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await api.post('/api/v1/ai-assistant/analyze-resource', {
        url: resourceUrl.trim(),
        type: detectResourceType(resourceUrl)
      });

      if (response.data.success) {
        const suggestions = response.data.suggestions;
        
        // Автозаполняем ответы на основе анализа
        setAnswers(prev => ({
          ...prev,
          product_service: suggestions.product_service || prev.product_service,
          target_audience: suggestions.target_audience || prev.target_audience,
          pain_points: suggestions.pain_points || prev.pain_points,
          tone: suggestions.tone || prev.tone,
          call_to_action: Array.isArray(suggestions.cta) ? suggestions.cta.join(', ') : (suggestions.cta || prev.call_to_action),
          keywords: suggestions.keywords || prev.keywords
        }));
        
        toast.success('Ресурс проанализирован! Поля заполнены автоматически.');
      } else {
        throw new Error(response.data.error || 'Не удалось проанализировать ресурс');
      }
    } catch (err) {
      console.error('Error analyzing resource:', err);
      toast.error(err.response?.data?.error || err.message || 'Не удалось проанализировать ресурс');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleNext = () => {
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleSkip = () => {
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      handleComplete();
    }
  };

  const handleComplete = () => {
    // Формируем данные для заполнения формы
    const formData = {
      title: answers.product_service || answers.niche || 'Новый пост',
      description: `Пост о ${answers.product_service || answers.niche}. ${answers.pain_points.length > 0 ? `Основные проблемы: ${answers.pain_points.join(', ')}.` : ''}`,
      target_audience: answers.target_audience,
      business_goals: answers.business_goals,
      platforms: answers.platforms,
      tone: answers.tone,
      call_to_action: answers.call_to_action ? [answers.call_to_action] : [],
      keywords: answers.keywords
    };

    onComplete(formData);
    onClose();
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <QuestionContainer>
            <QuestionTitle>Ниша, продукт или услуга</QuestionTitle>
            <QuestionHelp>О чем ваш бизнес? Что вы предлагаете?</QuestionHelp>
            <TextArea
              placeholder="Например: Установка видеонаблюдения для частных домов и офисов"
              value={answers.product_service}
              onChange={(e) => setAnswers({...answers, product_service: e.target.value})}
              autoFocus
            />
            
            <div style={{ marginTop: '1.5rem' }}>
              <QuestionTitle style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                <Link2 size={16} style={{ marginRight: '0.5rem', display: 'inline-block', verticalAlign: 'middle' }} />
                Или вставьте ссылку на ваш ресурс (сайт, Telegram, Instagram)
              </QuestionTitle>
              <ResourceInputGroup>
                <ResourceInput
                  type="url"
                  placeholder="https://example.com или https://t.me/channel"
                  value={resourceUrl}
                  onChange={(e) => setResourceUrl(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAnalyzeResource()}
                />
                <AnalyzeButton
                  onClick={handleAnalyzeResource}
                  disabled={!resourceUrl.trim() || isAnalyzing}
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Анализ...
                    </>
                  ) : (
                    <>
                      <Wand2 size={16} />
                      Анализировать
                    </>
                  )}
                </AnalyzeButton>
              </ResourceInputGroup>
            </div>
          </QuestionContainer>
        );

      case 2:
        return (
          <QuestionContainer>
            <QuestionTitle>Целевая аудитория</QuestionTitle>
            <QuestionHelp>Кто ваши клиенты? Опишите их портрет</QuestionHelp>
            <TextArea
              placeholder="Например: Владельцы частных домов, 35-55 лет, заботящиеся о безопасности"
              value={answers.target_audience}
              onChange={(e) => setAnswers({...answers, target_audience: e.target.value})}
              autoFocus
            />
            
            <div style={{ marginTop: '1.5rem' }}>
              <QuestionTitle>Основные боли аудитории</QuestionTitle>
              <QuestionHelp>Какие проблемы решает ваш продукт/услуга?</QuestionHelp>
              <TextArea
                placeholder="Введите через запятую или с новой строки. Например: Безопасность дома, Защита от воров, Контроль за детьми"
                value={answers.pain_points.join('\n')}
                onChange={(e) => {
                  const points = e.target.value.split('\n').filter(p => p.trim());
                  setAnswers({...answers, pain_points: points});
                }}
              />
            </div>
          </QuestionContainer>
        );

      case 3:
        return (
          <QuestionContainer>
            <QuestionTitle>Стиль общения</QuestionTitle>
            <QuestionHelp>Как вы обращаетесь к аудитории?</QuestionHelp>
            <OptionGroup style={{ marginBottom: '1.5rem' }}>
              <OptionButton
                selected={answers.formal_address === 'Вы'}
                onClick={() => setAnswers({...answers, formal_address: 'Вы'})}
              >
                На Вы
              </OptionButton>
              <OptionButton
                selected={answers.formal_address === 'Ты'}
                onClick={() => setAnswers({...answers, formal_address: 'Ты'})}
              >
                На Ты
              </OptionButton>
            </OptionGroup>
            
            <QuestionTitle style={{ marginTop: '1.5rem' }}>Тон контента</QuestionTitle>
            <QuestionHelp>Какой стиль текстов вам подходит?</QuestionHelp>
            <OptionGroup>
              {TONE_OPTIONS.map(option => (
                <OptionButton
                  key={option.value}
                  selected={answers.tone === option.value}
                  onClick={() => setAnswers({...answers, tone: option.value})}
                >
                  {option.label}
                </OptionButton>
              ))}
            </OptionGroup>
          </QuestionContainer>
        );

      case 4:
        return (
          <QuestionContainer>
            <QuestionTitle>Бизнес-цели</QuestionTitle>
            <QuestionHelp>Что вы хотите достичь этим контентом? (можно выбрать несколько)</QuestionHelp>
            <OptionGroup>
              {BUSINESS_GOALS.map(goal => (
                <OptionButton
                  key={goal}
                  selected={answers.business_goals.includes(goal)}
                  onClick={() => {
                    const newGoals = answers.business_goals.includes(goal)
                      ? answers.business_goals.filter(g => g !== goal)
                      : [...answers.business_goals, goal];
                    setAnswers({...answers, business_goals: newGoals});
                  }}
                >
                  {goal}
                </OptionButton>
              ))}
            </OptionGroup>
            
            <div style={{ marginTop: '1.5rem' }}>
              <QuestionTitle>Платформы для публикации</QuestionTitle>
              <QuestionHelp>Где будет опубликован контент?</QuestionHelp>
              <OptionGroup>
                <OptionButton
                  selected={answers.platforms.includes('telegram')}
                  onClick={() => {
                    const newPlatforms = answers.platforms.includes('telegram')
                      ? answers.platforms.filter(p => p !== 'telegram')
                      : [...answers.platforms, 'telegram'];
                    setAnswers({...answers, platforms: newPlatforms});
                  }}
                >
                  Telegram
                </OptionButton>
                <OptionButton
                  selected={answers.platforms.includes('instagram')}
                  onClick={() => {
                    const newPlatforms = answers.platforms.includes('instagram')
                      ? answers.platforms.filter(p => p !== 'instagram')
                      : [...answers.platforms, 'instagram'];
                    setAnswers({...answers, platforms: newPlatforms});
                  }}
                >
                  Instagram
                </OptionButton>
              </OptionGroup>
            </div>
          </QuestionContainer>
        );

      case 5:
        return (
          <QuestionContainer>
            <QuestionTitle>Призыв к действию (CTA)</QuestionTitle>
            <QuestionHelp>К чему вы призываете аудиторию?</QuestionHelp>
            <Input
              placeholder="Например: Оставить заявку, Подписаться на канал, Перейти на сайт"
              value={answers.call_to_action}
              onChange={(e) => setAnswers({...answers, call_to_action: e.target.value})}
              autoFocus
            />
            
            <div style={{ marginTop: '1.5rem' }}>
              <QuestionTitle>Ключевые слова</QuestionTitle>
              <QuestionHelp>Введите через запятую (опционально)</QuestionHelp>
              <Input
                placeholder="Например: видеонаблюдение, безопасность, камеры"
                value={answers.keywords.join(', ')}
                onChange={(e) => {
                  const keywords = e.target.value.split(',').map(k => k.trim()).filter(k => k);
                  setAnswers({...answers, keywords});
                }}
              />
            </div>
          </QuestionContainer>
        );

      default:
        return null;
    }
  };

  return (
    <ModalOverlay onClick={(e) => e.target === e.currentTarget && onClose()}>
      <ModalContent onClick={(e) => e.stopPropagation()}>
        <CloseButton onClick={onClose}>
          <X size={24} />
        </CloseButton>
        
        <Title>
          <Wand2 size={24} />
          AI Помощник
        </Title>
        <Subtitle>
          Ответьте на несколько вопросов, и мы автоматически заполним форму создания контента
        </Subtitle>
        
        <ProgressBar>
          <ProgressFill progress={progress} />
        </ProgressBar>
        
        {renderStep()}
        
        <ButtonGroup>
          {step > 1 && (
            <Button onClick={handleBack}>
              <ArrowLeft size={16} />
              Назад
            </Button>
          )}
          <SkipButton onClick={handleSkip} style={{ marginLeft: step === 1 ? 'auto' : '0' }}>
            Пропустить
          </SkipButton>
          <Button primary onClick={handleNext}>
            {step === totalSteps ? (
              <>
                <Check size={16} />
                Заполнить форму
              </>
            ) : (
              <>
                Далее
                <ArrowRight size={16} />
              </>
            )}
          </Button>
        </ButtonGroup>
      </ModalContent>
    </ModalOverlay>
  );
};

