import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useForm, Controller } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  ArrowLeft, 
  Wand2, 
  Upload, 
  Image as ImageIcon, 
  Send,
  Check,
  X
} from 'lucide-react';
import { contentAPI } from '../services/api';
import { useProject } from '../contexts/ProjectContext';

// --- Styled Components ---

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding-bottom: 4rem;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
`;

const BackButton = styled.button`
  background: none;
  border: none;
  color: ${props => props.theme.colors.textSecondary};
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  
  &:hover {
    background: ${props => props.theme.colors.backgroundTertiary};
    color: ${props => props.theme.colors.primary};
  }
`;

const Title = styled.h1`
  font-size: ${props => props.theme.fontSize['2xl']};
  color: ${props => props.theme.colors.text};
  margin: 0;
`;

const Card = styled.div`
  background: ${props => props.theme.colors.backgroundSecondary};
  border-radius: ${props => props.theme.borderRadius.lg};
  border: 1px solid ${props => props.theme.colors.border};
  padding: 2rem;
  box-shadow: ${props => props.theme.colors.shadow};
`;

const FormGroup = styled.div`
  margin-bottom: 1.5rem;
`;

const Label = styled.label`
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: ${props => props.theme.colors.text};
`;

const Input = styled.input`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  background: ${props => props.theme.colors.background};
  color: ${props => props.theme.colors.text};
  
  &:focus {
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 2px ${props => props.theme.colors.primaryLight};
  }
`;

const TextArea = styled.textarea`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  background: ${props => props.theme.colors.background};
  color: ${props => props.theme.colors.text};
  min-height: 120px;
  resize: vertical;
  
  &:focus {
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 2px ${props => props.theme.colors.primaryLight};
  }
`;

const CheckboxGroup = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid ${props => props.checked ? props.theme.colors.primary : props.theme.colors.border};
  background: ${props => props.checked ? props.theme.colors.primaryLight : props.theme.colors.background};
  color: ${props => props.checked ? props.theme.colors.primary : props.theme.colors.text};
  border-radius: ${props => props.theme.borderRadius.full};
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
  font-weight: 500;

  &:hover {
    border-color: ${props => props.theme.colors.primary};
  }

  input {
    display: none;
  }
`;

const Select = styled.select`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  background: ${props => props.theme.colors.background};
  color: ${props => props.theme.colors.text};
`;

const Button = styled.button`
  width: 100%;
  padding: 1rem;
  background: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  border-radius: ${props => props.theme.borderRadius.md};
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  
  &:hover {
    background: ${props => props.theme.colors.primaryHover};
  }
  
  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
`;

const ImageOptions = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-top: 0.5rem;
`;

const ImageOption = styled.label`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1rem;
  border: 2px solid ${props => props.checked ? props.theme.colors.primary : props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  cursor: pointer;
  background: ${props => props.checked ? props.theme.colors.primaryLight : props.theme.colors.background};
  transition: all 0.2s;

  &:hover {
    border-color: ${props => props.theme.colors.primary};
  }

  input {
    display: none;
  }
`;

const ToggleSwitch = styled.label`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  margin-top: 1rem;
  padding: 1rem;
  background: ${props => props.theme.colors.backgroundTertiary};
  border-radius: ${props => props.theme.borderRadius.md};
`;

// --- AI Modal Component ---

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
`;

const ModalContent = styled.div`
  background: ${props => props.theme.colors.background};
  padding: 2rem;
  border-radius: ${props => props.theme.borderRadius.lg};
  width: 90%;
  max-width: 500px;
  position: relative;
`;

const AIModal = ({ isOpen, onClose, onComplete }) => {
  const [step, setStep] = useState(1);
  const [answers, setAnswers] = useState({ topic: '', audience: '', goal: '' });

  if (!isOpen) return null;

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
    else {
      onComplete(answers);
      onClose();
    }
  };

  return (
    <ModalOverlay>
      <ModalContent>
        <h2 style={{ marginBottom: '1rem' }}>🤖 AI Помощник</h2>
        
        {step === 1 && (
          <div>
            <Label>О чем хотите написать?</Label>
            <Input 
              autoFocus
              placeholder="Например: Новые услуги монтажа..."
              value={answers.topic}
              onChange={e => setAnswers({...answers, topic: e.target.value})}
            />
          </div>
        )}

        {step === 2 && (
          <div>
            <Label>Для кого этот пост?</Label>
            <Input 
              autoFocus
              placeholder="Например: Владельцы частных домов..."
              value={answers.audience}
              onChange={e => setAnswers({...answers, audience: e.target.value})}
            />
          </div>
        )}

        {step === 3 && (
          <div>
            <Label>Какая главная цель?</Label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {['Продажи', 'Вовлечение', 'Информация'].map(g => (
                <Button 
                  key={g} 
                  type="button" 
                  onClick={() => {
                    setAnswers({...answers, goal: g});
                    onComplete({...answers, goal: g});
                    onClose();
                  }}
                  style={{ background: '#f0f0f0', color: '#333' }}
                >
                  {g}
                </Button>
              ))}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem' }}>
          {step > 1 && <Button type="button" onClick={() => setStep(step - 1)} style={{ width: 'auto', background: 'gray' }}>Назад</Button>}
          {step < 3 && <Button type="button" onClick={handleNext} style={{ width: 'auto', marginLeft: 'auto' }}>Далее</Button>}
        </div>
        
        <button 
          onClick={onClose} 
          style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', cursor: 'pointer' }}
        >
          <X size={24} />
        </button>
      </ModalContent>
    </ModalOverlay>
  );
};

// --- Main Page ---

const BUSINESS_GOALS = [
  'Продажи', 'Охват', 'Вовлечение', 'Лиды', 'Трафик', 'Бренд', 'Лояльность'
];

export const CreateContent = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { currentProject } = useProject();
  const [isAIModalOpen, setIsAIModalOpen] = useState(true); // Open by default
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { register, handleSubmit, control, setValue, watch, formState: { errors } } = useForm({
    defaultValues: {
      title: '',
      description: '',
      target_audience: currentProject?.settings?.target_audience || '',
      business_goals: [],
      tone: currentProject?.settings?.tone_of_voice || 'professional',
      platforms: ['telegram'],
      image_source: 'ai',
      publish_immediately: true
    }
  });

  const selectedImageSource = watch('image_source');
  const selectedPlatforms = watch('platforms');
  const selectedGoals = watch('business_goals');

  useEffect(() => {
    // Если режим AI передан в URL или проект выбран, можно открыть модалку
    // setIsAIModalOpen(true);
  }, []);

  const handleAIComplete = (data) => {
    setValue('title', data.topic);
    setValue('description', `Напиши пост на тему "${data.topic}". Цель: ${data.goal}.`);
    if (data.audience) setValue('target_audience', data.audience);
    if (data.goal && BUSINESS_GOALS.includes(data.goal)) {
        setValue('business_goals', [data.goal]);
    }
    toast.success('AI заполнил форму! Проверьте и дополните.');
  };

  const onSubmit = async (data) => {
    if (!currentProject) {
      toast.error('Выберите проект в сайдбаре!');
      return;
    }

    if (data.platforms.length === 0) {
      toast.error('Выберите хотя бы одну платформу!');
      return;
    }

    if (data.business_goals.length === 0) {
      toast.error('Выберите хотя бы одну бизнес-цель!');
      return;
    }

    try {
      setIsSubmitting(true);
      
      const payload = {
        ...data,
        project_id: currentProject.id,
        content_types: ['post'], // Хардкод пока что
        generate_image: data.image_source === 'ai',
        // Upload logic would go here (upload file -> get ID -> uploaded_files: [id])
      };

      await contentAPI.createContent(payload);
      toast.success('Контент создан и отправлен в работу!');
      navigate('/dashboard/content');
    } catch (error) {
      console.error(error);
      toast.error('Ошибка создания: ' + (error.response?.data?.message || error.message));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Container>
      <AIModal 
        isOpen={isAIModalOpen} 
        onClose={() => setIsAIModalOpen(false)} 
        onComplete={handleAIComplete} 
      />

      <Header>
        <BackButton onClick={() => navigate(-1)}>
          <ArrowLeft size={24} />
        </BackButton>
        <Title>Создание контента</Title>
        <Button 
            type="button" 
            onClick={() => setIsAIModalOpen(true)} 
            style={{ width: 'auto', marginLeft: 'auto', padding: '0.5rem 1rem', fontSize: '0.9rem' }}
        >
            <Wand2 size={16} /> AI Помощник
        </Button>
      </Header>

      <Card>
        <form onSubmit={handleSubmit(onSubmit)}>
          
          <FormGroup>
            <Label>Заголовок / Тема</Label>
            <Input 
              {...register('title', { required: 'Обязательно' })} 
              placeholder="О чем будет пост?" 
            />
            {errors.title && <span style={{color:'red', fontSize:'0.8rem'}}>{errors.title.message}</span>}
          </FormGroup>

          <FormGroup>
            <Label>Бизнес-цели (выберите несколько)</Label>
            <Controller
              name="business_goals"
              control={control}
              render={({ field }) => (
                <CheckboxGroup>
                  {BUSINESS_GOALS.map(goal => (
                    <CheckboxLabel key={goal} checked={field.value.includes(goal)}>
                      <input
                        type="checkbox"
                        value={goal}
                        checked={field.value.includes(goal)}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          const newValue = checked
                            ? [...field.value, goal]
                            : field.value.filter(v => v !== goal);
                          field.onChange(newValue);
                        }}
                      />
                      {goal}
                    </CheckboxLabel>
                  ))}
                </CheckboxGroup>
              )}
            />
          </FormGroup>

          <FormGroup>
            <Label>Платформы для публикации</Label>
            <Controller
              name="platforms"
              control={control}
              render={({ field }) => (
                <CheckboxGroup>
                  <CheckboxLabel checked={field.value.includes('telegram')}>
                    <input
                      type="checkbox"
                      value="telegram"
                      checked={field.value.includes('telegram')}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        const newValue = checked
                          ? [...field.value, 'telegram']
                          : field.value.filter(v => v !== 'telegram');
                        field.onChange(newValue);
                      }}
                    />
                    Telegram
                  </CheckboxLabel>
                  <CheckboxLabel checked={field.value.includes('instagram')}>
                    <input
                      type="checkbox"
                      value="instagram"
                      checked={field.value.includes('instagram')}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        const newValue = checked
                          ? [...field.value, 'instagram']
                          : field.value.filter(v => v !== 'instagram');
                        field.onChange(newValue);
                      }}
                    />
                    Instagram
                  </CheckboxLabel>
                </CheckboxGroup>
              )}
            />
          </FormGroup>

          <FormGroup>
            <Label>Описание / Ключевые мысли</Label>
            <TextArea 
              {...register('description', { required: 'Опишите суть' })} 
              placeholder="Тезисы, мысли, о чем нужно рассказать..."
            />
          </FormGroup>

          <FormGroup>
            <Label>Целевая аудитория</Label>
            <TextArea 
              {...register('target_audience')} 
              placeholder="Кто будет читать?"
              rows={3}
              style={{ minHeight: '80px' }}
            />
          </FormGroup>

          <FormGroup>
            <Label>Изображение</Label>
            <Controller
              name="image_source"
              control={control}
              render={({ field }) => (
                <ImageOptions>
                  <ImageOption checked={field.value === 'ai'}>
                    <input {...field} type="radio" value="ai" />
                    <Wand2 size={24} />
                    <span>AI Генерация</span>
                  </ImageOption>
                  <ImageOption checked={field.value === 'stock'}>
                    <input {...field} type="radio" value="stock" />
                    <ImageIcon size={24} />
                    <span>Стоки</span>
                  </ImageOption>
                  <ImageOption checked={field.value === 'upload'}>
                    <input {...field} type="radio" value="upload" />
                    <Upload size={24} />
                    <span>Загрузить</span>
                  </ImageOption>
                </ImageOptions>
              )}
            />
            {selectedImageSource === 'upload' && (
                <div style={{ marginTop: '1rem', padding: '1rem', border: '1px dashed gray', borderRadius: '8px', textAlign: 'center' }}>
                    <p>Функция загрузки файла (в разработке)</p>
                    {/* Здесь будет <input type="file" /> */}
                </div>
            )}
          </FormGroup>

          <FormGroup>
            <ToggleSwitch>
              <input type="checkbox" {...register('publish_immediately')} />
              <div>
                <div style={{ fontWeight: 600 }}>Опубликовать сразу</div>
                <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>Если выключено — сохранится как черновик</div>
              </div>
            </ToggleSwitch>
          </FormGroup>

          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Создаем...' : (
                <>
                    <Send size={20} /> Создать контент
                </>
            )}
          </Button>

        </form>
      </Card>
    </Container>
  );
};

