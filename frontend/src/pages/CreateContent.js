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
  Send
} from 'lucide-react';
import { contentAPI } from '../services/api';
import api from '../services/api';
import { useProject } from '../contexts/ProjectContext';
import { SmartAIModal } from '../components/SmartAIModal';
import { ContentVariantsPreview } from '../components/ContentVariantsPreview';

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

// --- AI Modal Component удален, используется SmartAIModal из components ---

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
  const [uploadedFileId, setUploadedFileId] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [showVariants, setShowVariants] = useState(false);
  const [contentVariants, setContentVariants] = useState([]);
  const [workflowId, setWorkflowId] = useState(null);

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
    // Заполняем форму на основе ответов из опросника
    if (data.title) setValue('title', data.title);
    if (data.description) setValue('description', data.description);
    if (data.target_audience) setValue('target_audience', data.target_audience);
    if (data.business_goals && data.business_goals.length > 0) {
      setValue('business_goals', data.business_goals);
    }
    if (data.platforms && data.platforms.length > 0) {
      setValue('platforms', data.platforms);
    }
    if (data.tone) setValue('tone', data.tone);
    if (data.call_to_action && data.call_to_action.length > 0) {
      // call_to_action может быть массивом или строкой
      const ctaValue = Array.isArray(data.call_to_action) 
        ? data.call_to_action[0] 
        : data.call_to_action;
      // Сохраняем в description если нужно, или в отдельное поле если есть
      const currentDesc = watch('description') || '';
      if (ctaValue && !currentDesc.includes(ctaValue)) {
        setValue('description', `${currentDesc}\n\nПризыв к действию: ${ctaValue}`);
      }
    }
    if (data.keywords && data.keywords.length > 0) {
      // Ключевые слова можно добавить в description
      const currentDesc = watch('description') || '';
      const keywordsText = data.keywords.join(', ');
      if (!currentDesc.includes(keywordsText)) {
        setValue('description', `${currentDesc}\n\nКлючевые слова: ${keywordsText}`);
      }
    }
    toast.success('Форма заполнена на основе ваших ответов! Проверьте и дополните при необходимости.');
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

    // Проверка минимальной длины description
    if (!data.description || data.description.trim().length < 10) {
      toast.error('Описание должно содержать минимум 10 символов');
      return;
    }

    try {
      setIsSubmitting(true);
      
      const payload = {
        title: data.title,
        description: data.description,
        target_audience: data.target_audience || '',
        business_goals: data.business_goals,
        call_to_action: [], // Обязательное поле, даже если пустое
        tone: data.tone || 'professional',
        keywords: [], // Можно добавить позже
        platforms: data.platforms,
        content_types: ['post'],
        project_id: currentProject.id,
        generate_image: data.image_source === 'ai',
        image_source: data.image_source === 'ai' ? 'ai' : (data.image_source === 'stock' ? 'stock' : null),
        publish_immediately: false, // Не публикуем сразу, показываем варианты для выбора
        uploaded_files: uploadedFileId ? [uploadedFileId] : [], // ID загруженного файла
        variants_count: 3 // Генерируем 3 варианта для выбора
      };

      const response = await contentAPI.createContent(payload);
      
      // Если есть варианты в ответе - показываем их для выбора
      if (response.result?.results) {
        // Ищем результаты DraftingAgent с вариантами
        const draftingResults = Object.values(response.result.results).find(
          r => r.variants && r.variants.length > 0
        );
        
        if (draftingResults && draftingResults.variants) {
          setContentVariants(draftingResults.variants);
          setWorkflowId(response.workflow_id);
          setShowVariants(true);
          toast.success('Создано вариантов: ' + draftingResults.variants.length);
        } else {
          // Если вариантов нет - публикуем как обычно
          toast.success('Контент создан и отправлен в работу!');
          navigate('/dashboard/content');
        }
      } else {
        toast.success('Контент создан и отправлен в работу!');
        navigate('/dashboard/content');
      }
    } catch (error) {
      console.error(error);
      toast.error('Ошибка создания: ' + (error.response?.data?.message || error.message));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVariantSelect = async (variant, workflowId) => {
    // TODO: Реализовать публикацию выбранного варианта
    // Пока просто закрываем модалку и переходим на страницу контента
    console.log('Selected variant:', variant, 'Workflow ID:', workflowId);
    navigate('/dashboard/content');
  };

  return (
    <Container>
      <SmartAIModal 
        isOpen={isAIModalOpen} 
        onClose={() => setIsAIModalOpen(false)} 
        onComplete={handleAIComplete} 
      />
      
      <ContentVariantsPreview
        isOpen={showVariants}
        onClose={() => {
          setShowVariants(false);
          navigate('/dashboard/content');
        }}
        variants={contentVariants}
        workflowId={workflowId}
        onSelectVariant={handleVariantSelect}
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
              {...register('description', { 
                required: 'Опишите суть',
                minLength: {
                  value: 10,
                  message: 'Описание должно содержать минимум 10 символов'
                }
              })} 
              placeholder="Тезисы, мысли, о чем нужно рассказать..."
            />
            {errors.description && <span style={{color:'red', fontSize:'0.8rem'}}>{errors.description.message}</span>}
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
                <div style={{ marginTop: '1rem' }}>
                    <input
                        type="file"
                        accept="image/*"
                        disabled={isUploading}
                        onChange={async (e) => {
                            const file = e.target.files?.[0];
                            if (!file) return;
                            
                            // Проверка размера (10MB)
                            const maxSize = 10 * 1024 * 1024;
                            if (file.size > maxSize) {
                                toast.error('Файл слишком большой. Максимальный размер: 10MB');
                                return;
                            }
                            
                            setIsUploading(true);
                            try {
                                const formData = new FormData();
                                formData.append('file', file);
                                
                                const response = await api.post('/api/v1/upload', formData, {
                                    headers: {
                                        'Content-Type': 'multipart/form-data'
                                    }
                                });
                                
                                if (response.data.success) {
                                    setUploadedFileId(response.data.file_id);
                                    setValue('uploaded_file_id', response.data.file_id);
                                    toast.success(`Файл ${file.name} успешно загружен!`);
                                } else {
                                    throw new Error(response.data.message || 'Ошибка загрузки файла');
                                }
                            } catch (error) {
                                console.error('Error uploading file:', error);
                                toast.error(error.response?.data?.message || error.message || 'Не удалось загрузить файл');
                            } finally {
                                setIsUploading(false);
                            }
                        }}
                        style={{ 
                            width: '100%',
                            padding: '0.75rem',
                            border: '1px dashed',
                            borderColor: 'var(--border-color, #ccc)',
                            borderRadius: '8px',
                            cursor: isUploading ? 'not-allowed' : 'pointer',
                            opacity: isUploading ? 0.6 : 1
                        }}
                    />
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #666)', marginTop: '0.5rem' }}>
                        {isUploading ? 'Загрузка...' : 'Выберите изображение с компьютера (JPG, PNG, GIF, до 10MB)'}
                    </p>
                    {uploadedFileId && (
                        <p style={{ fontSize: '0.8rem', color: 'green', marginTop: '0.5rem' }}>
                            ✓ Файл загружен
                        </p>
                    )}
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

