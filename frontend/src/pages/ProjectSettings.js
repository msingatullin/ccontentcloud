/**
 * ProjectSettings - Страница настроек проекта
 * Вкладки: AI Контекст и Подключения
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { toast } from 'react-hot-toast';
import {
  Settings,
  Brain,
  Link2,
  Save,
  ArrowLeft,
  Plus,
  X,
  Send,
  Instagram,
  Check,
  Loader2
} from 'lucide-react';
import { projectsAPI, telegramAPI, instagramAPI } from '../services/api';
import api from '../services/api';
import { useProject } from '../contexts/ProjectContext';

// Styled Components
const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.xl};
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
`;

const BackButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: ${props => props.theme.colors.backgroundSecondary};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  color: ${props => props.theme.colors.textSecondary};
  cursor: pointer;
  transition: all ${props => props.theme.transitions.normal};

  &:hover {
    background: ${props => props.theme.colors.backgroundTertiary};
    color: ${props => props.theme.colors.text};
  }
`;

const Title = styled.h1`
  font-size: ${props => props.theme.fontSize['2xl']};
  font-weight: ${props => props.theme.fontWeight.bold};
  color: ${props => props.theme.colors.text};
  margin: 0;
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
`;

const TabsContainer = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.sm};
  border-bottom: 1px solid ${props => props.theme.colors.border};
  padding-bottom: ${props => props.theme.spacing.md};
`;

const Tab = styled.button`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  padding: ${props => props.theme.spacing.md} ${props => props.theme.spacing.lg};
  background: ${props => props.$active ? props.theme.colors.primaryLight : 'transparent'};
  border: none;
  border-radius: ${props => props.theme.borderRadius.md};
  color: ${props => props.$active ? props.theme.colors.primary : props.theme.colors.textSecondary};
  font-weight: ${props => props.$active ? props.theme.fontWeight.semibold : props.theme.fontWeight.medium};
  cursor: pointer;
  transition: all ${props => props.theme.transitions.normal};

  &:hover {
    background: ${props => props.$active ? props.theme.colors.primaryLight : props.theme.colors.backgroundTertiary};
  }
`;

const TabContent = styled.div`
  background: ${props => props.theme.colors.backgroundSecondary};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.lg};
  padding: ${props => props.theme.spacing.xl};
`;

const FormGroup = styled.div`
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const Label = styled.label`
  display: block;
  font-size: ${props => props.theme.fontSize.sm};
  font-weight: ${props => props.theme.fontWeight.medium};
  color: ${props => props.theme.colors.text};
  margin-bottom: ${props => props.theme.spacing.sm};
`;

const HelpText = styled.p`
  font-size: ${props => props.theme.fontSize.xs};
  color: ${props => props.theme.colors.textSecondary};
  margin-top: ${props => props.theme.spacing.xs};
`;

const Input = styled.input`
  width: 100%;
  padding: ${props => props.theme.spacing.md};
  background: ${props => props.theme.colors.background};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  color: ${props => props.theme.colors.text};
  font-size: ${props => props.theme.fontSize.base};

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 2px ${props => props.theme.colors.primaryLight};
  }

  &::placeholder {
    color: ${props => props.theme.colors.textTertiary};
  }
`;

const Textarea = styled.textarea`
  width: 100%;
  min-height: 120px;
  padding: ${props => props.theme.spacing.md};
  background: ${props => props.theme.colors.background};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  color: ${props => props.theme.colors.text};
  font-size: ${props => props.theme.fontSize.base};
  resize: vertical;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 2px ${props => props.theme.colors.primaryLight};
  }

  &::placeholder {
    color: ${props => props.theme.colors.textTertiary};
  }
`;

const Select = styled.select`
  width: 100%;
  padding: ${props => props.theme.spacing.md};
  background: ${props => props.theme.colors.background};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  color: ${props => props.theme.colors.text};
  font-size: ${props => props.theme.fontSize.base};
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 2px ${props => props.theme.colors.primaryLight};
  }
`;

const TagsInput = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: ${props => props.theme.spacing.sm};
  padding: ${props => props.theme.spacing.sm};
  background: ${props => props.theme.colors.background};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  min-height: 48px;

  &:focus-within {
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 2px ${props => props.theme.colors.primaryLight};
  }
`;

const Tag = styled.span`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.xs};
  padding: ${props => props.theme.spacing.xs} ${props => props.theme.spacing.sm};
  background: ${props => props.theme.colors.primaryLight};
  color: ${props => props.theme.colors.primary};
  border-radius: ${props => props.theme.borderRadius.full};
  font-size: ${props => props.theme.fontSize.sm};
`;

const TagRemove = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  background: transparent;
  border: none;
  color: ${props => props.theme.colors.primary};
  cursor: pointer;
  padding: 0;

  &:hover {
    color: ${props => props.theme.colors.error};
  }
`;

const TagInput = styled.input`
  flex: 1;
  min-width: 100px;
  border: none;
  background: transparent;
  color: ${props => props.theme.colors.text};
  font-size: ${props => props.theme.fontSize.sm};
  padding: ${props => props.theme.spacing.xs};

  &:focus {
    outline: none;
  }

  &::placeholder {
    color: ${props => props.theme.colors.textTertiary};
  }
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  padding: ${props => props.theme.spacing.md} ${props => props.theme.spacing.lg};
  background: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  border-radius: ${props => props.theme.borderRadius.md};
  font-weight: ${props => props.theme.fontWeight.medium};
  cursor: pointer;
  transition: all ${props => props.theme.transitions.normal};

  &:hover:not(:disabled) {
    background: ${props => props.theme.colors.primaryHover};
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const SecondaryButton = styled(Button)`
  background: ${props => props.theme.colors.backgroundTertiary};
  color: ${props => props.theme.colors.text};

  &:hover:not(:disabled) {
    background: ${props => props.theme.colors.border};
  }
`;

// Integrations Tab Styles
const Section = styled.div`
  margin-bottom: ${props => props.theme.spacing.xl};

  &:last-child {
    margin-bottom: 0;
  }
`;

const SectionHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${props => props.theme.spacing.md};
`;

const SectionTitle = styled.h3`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  font-size: ${props => props.theme.fontSize.lg};
  font-weight: ${props => props.theme.fontWeight.semibold};
  color: ${props => props.theme.colors.text};
  margin: 0;
`;

const ChannelList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.sm};
`;

const ChannelItem = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
  padding: ${props => props.theme.spacing.md};
  background: ${props => props.theme.colors.background};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
`;

const ChannelIcon = styled.div`
  width: 40px;
  height: 40px;
  background: ${props => props.$platform === 'telegram' ? '#0088cc' : '#E4405F'};
  border-radius: ${props => props.theme.borderRadius.md};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
`;

const ChannelInfo = styled.div`
  flex: 1;
`;

const ChannelName = styled.div`
  font-weight: ${props => props.theme.fontWeight.medium};
  color: ${props => props.theme.colors.text};
`;

const ChannelMeta = styled.div`
  font-size: ${props => props.theme.fontSize.xs};
  color: ${props => props.theme.colors.textSecondary};
`;

const RemoveButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.sm};
  color: ${props => props.theme.colors.textSecondary};
  cursor: pointer;
  transition: all ${props => props.theme.transitions.normal};

  &:hover {
    background: ${props => props.theme.colors.errorLight};
    border-color: ${props => props.theme.colors.error};
    color: ${props => props.theme.colors.error};
  }
`;

const EmptyState = styled.div`
  padding: ${props => props.theme.spacing.xl};
  text-align: center;
  color: ${props => props.theme.colors.textSecondary};
  background: ${props => props.theme.colors.background};
  border: 1px dashed ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
`;

// Modal Styles
const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: ${props => props.theme.zIndex.modal};
`;

const Modal = styled.div`
  background: ${props => props.theme.colors.backgroundSecondary};
  border-radius: ${props => props.theme.borderRadius.lg};
  padding: ${props => props.theme.spacing.xl};
  width: 100%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
`;

const ModalHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const ModalTitle = styled.h3`
  font-size: ${props => props.theme.fontSize.lg};
  font-weight: ${props => props.theme.fontWeight.semibold};
  color: ${props => props.theme.colors.text};
  margin: 0;
`;

const CloseButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  color: ${props => props.theme.colors.textSecondary};
  cursor: pointer;

  &:hover {
    color: ${props => props.theme.colors.text};
  }
`;

const SelectableItem = styled.button`
  width: 100%;
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
  padding: ${props => props.theme.spacing.md};
  background: ${props => props.$selected ? props.theme.colors.primaryLight : props.theme.colors.background};
  border: 1px solid ${props => props.$selected ? props.theme.colors.primary : props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  cursor: pointer;
  transition: all ${props => props.theme.transitions.normal};
  text-align: left;
  margin-bottom: ${props => props.theme.spacing.sm};

  &:hover {
    border-color: ${props => props.theme.colors.primary};
  }
`;

const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: ${props => props.theme.spacing.xxxl};
  color: ${props => props.theme.colors.textSecondary};
`;

const TONE_OPTIONS = [
  { value: 'professional', label: 'Профессиональный' },
  { value: 'friendly', label: 'Дружелюбный' },
  { value: 'casual', label: 'Разговорный' },
  { value: 'bold', label: 'Дерзкий' },
  { value: 'formal', label: 'Официальный' },
  { value: 'humorous', label: 'С юмором' },
  { value: 'custom', label: 'Свой вариант...' },
];

export const ProjectSettings = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { refreshProjects, updateProject: updateProjectContext } = useProject();
  
  const [activeTab, setActiveTab] = useState('ai');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [project, setProject] = useState(null);
  
  // AI Settings form
  const [businessDescription, setBusinessDescription] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [toneOfVoice, setToneOfVoice] = useState('professional');
  const [customTone, setCustomTone] = useState('');
  const [keywords, setKeywords] = useState([]);
  const [keywordInput, setKeywordInput] = useState('');
  const [resourceUrl, setResourceUrl] = useState('');
  const [isAnalyzingResource, setIsAnalyzingResource] = useState(false);
  
  // Integrations
  const [telegramChannels, setTelegramChannels] = useState([]);
  const [instagramAccounts, setInstagramAccounts] = useState([]);
  const [allTelegramChannels, setAllTelegramChannels] = useState([]);
  const [allInstagramAccounts, setAllInstagramAccounts] = useState([]);
  const [showTelegramModal, setShowTelegramModal] = useState(false);
  const [showInstagramModal, setShowInstagramModal] = useState(false);

  // Загрузка проекта
  const loadProject = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await projectsAPI.get(id);
      const proj = data.project || data;
      setProject(proj);
      
      // Заполняем форму из settings
      const settings = proj.settings || {};
      setBusinessDescription(settings.business_description || '');
      setTargetAudience(settings.target_audience || '');
      setToneOfVoice(settings.tone_of_voice || 'professional');
      setCustomTone(settings.custom_tone || '');
      setKeywords(settings.keywords || []);
      setResourceUrl(settings.resource_url || '');
    } catch (err) {
      console.error('Error loading project:', err);
      toast.error('Не удалось загрузить проект');
      navigate('/dashboard');
    } finally {
      setIsLoading(false);
    }
  }, [id, navigate]);

  // Загрузка каналов
  const loadChannels = useCallback(async () => {
    try {
      // Загружаем каналы проекта
      const telegramData = await telegramAPI.getChannels(id);
      setTelegramChannels(telegramData.channels || []);
      
      // Загружаем все каналы пользователя
      const allTelegramData = await telegramAPI.getChannels();
      setAllTelegramChannels(allTelegramData.channels || []);
    } catch (err) {
      console.error('Error loading channels:', err);
    }

    try {
      const instagramData = await instagramAPI.getAccounts(id);
      setInstagramAccounts(instagramData.accounts || []);
      
      const allInstagramData = await instagramAPI.getAccounts();
      setAllInstagramAccounts(allInstagramData.accounts || []);
    } catch (err) {
      console.error('Error loading Instagram accounts:', err);
    }
  }, [id]);

  useEffect(() => {
    loadProject();
    loadChannels();
  }, [loadProject, loadChannels]);

  // Анализ ресурса для автозаполнения
  const handleAnalyzeResource = async () => {
    if (!resourceUrl.trim()) {
      toast.error('Введите URL ресурса');
      return;
    }
    
    setIsAnalyzingResource(true);
    try {
      const response = await api.post('/api/v1/ai-assistant/analyze-resource', {
        url: resourceUrl.trim()
      });
      
      const data = response.data;
      
      if (!data.success) {
        throw new Error(data.error || 'Не удалось проанализировать ресурс');
      }
      
      const suggestions = data.suggestions || {};
      
      // Автозаполняем поля на основе анализа
      if (suggestions.product_service) {
        setBusinessDescription(suggestions.product_service);
      }
      if (suggestions.target_audience) {
        setTargetAudience(suggestions.target_audience);
      }
      if (suggestions.tone) {
        // Преобразуем tone в tone_of_voice
        const toneMapping = {
          'professional': 'professional',
          'casual': 'casual',
          'friendly': 'friendly',
          'authoritative': 'professional'
        };
        setToneOfVoice(toneMapping[suggestions.tone] || 'professional');
      }
      if (suggestions.keywords && suggestions.keywords.length > 0) {
        setKeywords(suggestions.keywords);
      }
      
      toast.success('Настройки заполнены на основе анализа ресурса!');
    } catch (err) {
      console.error('Error analyzing resource:', err);
      toast.error(err.response?.data?.error || err.message || 'Не удалось проанализировать ресурс');
    } finally {
      setIsAnalyzingResource(false);
    }
  };

  // Сохранение настроек AI
  const handleSaveSettings = async () => {
    try {
      setIsSaving(true);
      
      const settings = {
        business_description: businessDescription,
        target_audience: targetAudience,
        tone_of_voice: toneOfVoice,
        custom_tone: toneOfVoice === 'custom' ? customTone : '',
        keywords: keywords,
        resource_url: resourceUrl, // Сохраняем resource_url
      };

      await projectsAPI.update(id, { settings });
      await refreshProjects();
      
      toast.success('Настройки сохранены!');
    } catch (err) {
      console.error('Error saving settings:', err);
      toast.error('Не удалось сохранить настройки');
    } finally {
      setIsSaving(false);
    }
  };

  // Работа с тегами
  const handleAddKeyword = (e) => {
    if (e.key === 'Enter' && keywordInput.trim()) {
      e.preventDefault();
      if (!keywords.includes(keywordInput.trim())) {
        setKeywords([...keywords, keywordInput.trim()]);
      }
      setKeywordInput('');
    }
  };

  const handleRemoveKeyword = (keyword) => {
    setKeywords(keywords.filter(k => k !== keyword));
  };

  // Привязка/отвязка каналов
  const handleAssignTelegram = async (channelId) => {
    try {
      await telegramAPI.assignToProject(channelId, parseInt(id));
      await loadChannels();
      setShowTelegramModal(false);
      toast.success('Канал привязан к проекту');
    } catch (err) {
      console.error('Error assigning channel:', err);
      toast.error('Не удалось привязать канал');
    }
  };

  const handleUnassignTelegram = async (channelId) => {
    try {
      await telegramAPI.unassignFromProject(channelId);
      await loadChannels();
      toast.success('Канал отвязан от проекта');
    } catch (err) {
      console.error('Error unassigning channel:', err);
      toast.error('Не удалось отвязать канал');
    }
  };

  const handleAssignInstagram = async (accountId) => {
    try {
      await instagramAPI.assignToProject(accountId, parseInt(id));
      await loadChannels();
      setShowInstagramModal(false);
      toast.success('Аккаунт привязан к проекту');
    } catch (err) {
      console.error('Error assigning account:', err);
      toast.error('Не удалось привязать аккаунт');
    }
  };

  const handleUnassignInstagram = async (accountId) => {
    try {
      await instagramAPI.unassignFromProject(accountId);
      await loadChannels();
      toast.success('Аккаунт отвязан от проекта');
    } catch (err) {
      console.error('Error unassigning account:', err);
      toast.error('Не удалось отвязать аккаунт');
    }
  };

  // Свободные каналы (не привязаны к другим проектам)
  const availableTelegramChannels = allTelegramChannels.filter(
    ch => !ch.project_id || ch.project_id === parseInt(id)
  );
  
  const availableInstagramAccounts = allInstagramAccounts.filter(
    acc => !acc.project_id || acc.project_id === parseInt(id)
  );

  if (isLoading) {
    return (
      <Container>
        <LoadingContainer>
          <Loader2 size={32} className="animate-spin" />
        </LoadingContainer>
      </Container>
    );
  }

  return (
    <Container>
      <Header>
        <BackButton onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={20} />
        </BackButton>
        <Title>
          <Settings size={28} />
          Настройки: {project?.name}
        </Title>
      </Header>

      <TabsContainer>
        <Tab $active={activeTab === 'ai'} onClick={() => setActiveTab('ai')}>
          <Brain size={18} />
          AI Контекст
        </Tab>
        <Tab $active={activeTab === 'integrations'} onClick={() => setActiveTab('integrations')}>
          <Link2 size={18} />
          Подключения
        </Tab>
      </TabsContainer>

      {activeTab === 'ai' && (
        <TabContent>
          <FormGroup>
            <Label>Ссылка на ваш ресурс (опционально)</Label>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Input
                type="url"
                value={resourceUrl}
                onChange={(e) => setResourceUrl(e.target.value)}
                placeholder="https://example.com или https://t.me/channel"
                style={{ flex: 1 }}
              />
              <Button
                type="button"
                onClick={handleAnalyzeResource}
                disabled={!resourceUrl.trim() || isAnalyzingResource}
                style={{ width: 'auto', padding: '0.75rem 1.5rem' }}
              >
                {isAnalyzingResource ? (
                  <>
                    <Loader2 size={16} className="animate-spin" style={{ marginRight: '0.5rem' }} />
                    Анализирую...
                  </>
                ) : (
                  <>
                    🤖 Проанализировать
                  </>
                )}
              </Button>
            </div>
            <HelpText>
              AI изучит ваш ресурс и автоматически заполнит настройки проекта
            </HelpText>
          </FormGroup>

          <FormGroup>
            <Label>Описание бизнеса / проекта</Label>
            <Textarea
              value={businessDescription}
              onChange={(e) => setBusinessDescription(e.target.value)}
              placeholder="О чем ваш проект? Какие продукты/услуги вы предлагаете? Чем вы отличаетесь от конкурентов?"
            />
            <HelpText>
              AI будет использовать это описание для создания релевантного контента
            </HelpText>
          </FormGroup>

          <FormGroup>
            <Label>Целевая аудитория</Label>
            <Input
              value={targetAudience}
              onChange={(e) => setTargetAudience(e.target.value)}
              placeholder="Например: предприниматели 25-45 лет, интересующиеся инвестициями"
            />
            <HelpText>
              Опишите вашу целевую аудиторию: возраст, интересы, профессия
            </HelpText>
          </FormGroup>

          <FormGroup>
            <Label>Tone of Voice (стиль общения)</Label>
            <Select
              value={toneOfVoice}
              onChange={(e) => setToneOfVoice(e.target.value)}
            >
              {TONE_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </Select>
            {toneOfVoice === 'custom' && (
              <Input
                style={{ marginTop: '8px' }}
                value={customTone}
                onChange={(e) => setCustomTone(e.target.value)}
                placeholder="Опишите желаемый стиль общения..."
              />
            )}
          </FormGroup>

          <FormGroup>
            <Label>Ключевые слова и темы</Label>
            <TagsInput>
              {keywords.map((keyword, index) => (
                <Tag key={index}>
                  {keyword}
                  <TagRemove onClick={() => handleRemoveKeyword(keyword)}>
                    <X size={12} />
                  </TagRemove>
                </Tag>
              ))}
              <TagInput
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={handleAddKeyword}
                placeholder="Введите тему и нажмите Enter..."
              />
            </TagsInput>
            <HelpText>
              О чем писать? Добавьте ключевые темы для контента
            </HelpText>
          </FormGroup>

          <Button onClick={handleSaveSettings} disabled={isSaving}>
            {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            Сохранить настройки
          </Button>
        </TabContent>
      )}

      {activeTab === 'integrations' && (
        <TabContent>
          <Section>
            <SectionHeader>
              <SectionTitle>
                <Send size={20} />
                Telegram каналы
              </SectionTitle>
              <SecondaryButton onClick={() => setShowTelegramModal(true)}>
                <Plus size={16} />
                Привязать канал
              </SecondaryButton>
            </SectionHeader>

            {telegramChannels.length === 0 ? (
              <EmptyState>
                Нет привязанных Telegram каналов.<br />
                Нажмите "Привязать канал" чтобы добавить.
              </EmptyState>
            ) : (
              <ChannelList>
                {telegramChannels.map(channel => (
                  <ChannelItem key={channel.id}>
                    <ChannelIcon $platform="telegram">
                      <Send size={18} />
                    </ChannelIcon>
                    <ChannelInfo>
                      <ChannelName>{channel.name || channel.channel_name}</ChannelName>
                      <ChannelMeta>@{channel.username || channel.channel_id}</ChannelMeta>
                    </ChannelInfo>
                    <RemoveButton onClick={() => handleUnassignTelegram(channel.id)}>
                      <X size={16} />
                    </RemoveButton>
                  </ChannelItem>
                ))}
              </ChannelList>
            )}
          </Section>

          <Section>
            <SectionHeader>
              <SectionTitle>
                <Instagram size={20} />
                Instagram аккаунты
              </SectionTitle>
              <SecondaryButton onClick={() => setShowInstagramModal(true)}>
                <Plus size={16} />
                Привязать аккаунт
              </SecondaryButton>
            </SectionHeader>

            {instagramAccounts.length === 0 ? (
              <EmptyState>
                Нет привязанных Instagram аккаунтов.<br />
                Нажмите "Привязать аккаунт" чтобы добавить.
              </EmptyState>
            ) : (
              <ChannelList>
                {instagramAccounts.map(account => (
                  <ChannelItem key={account.id}>
                    <ChannelIcon $platform="instagram">
                      <Instagram size={18} />
                    </ChannelIcon>
                    <ChannelInfo>
                      <ChannelName>{account.name || account.username}</ChannelName>
                      <ChannelMeta>@{account.username}</ChannelMeta>
                    </ChannelInfo>
                    <RemoveButton onClick={() => handleUnassignInstagram(account.id)}>
                      <X size={16} />
                    </RemoveButton>
                  </ChannelItem>
                ))}
              </ChannelList>
            )}
          </Section>
        </TabContent>
      )}

      {/* Telegram Modal */}
      {showTelegramModal && (
        <ModalOverlay onClick={() => setShowTelegramModal(false)}>
          <Modal onClick={e => e.stopPropagation()}>
            <ModalHeader>
              <ModalTitle>Выберите Telegram канал</ModalTitle>
              <CloseButton onClick={() => setShowTelegramModal(false)}>
                <X size={20} />
              </CloseButton>
            </ModalHeader>

            {availableTelegramChannels.length === 0 ? (
              <EmptyState>
                Нет доступных каналов.<br />
                Добавьте канал в разделе "Настройки → Telegram".
              </EmptyState>
            ) : (
              availableTelegramChannels.map(channel => {
                const isAssigned = channel.project_id === parseInt(id);
                return (
                  <SelectableItem
                    key={channel.id}
                    $selected={isAssigned}
                    onClick={() => !isAssigned && handleAssignTelegram(channel.id)}
                    disabled={isAssigned}
                  >
                    <ChannelIcon $platform="telegram">
                      <Send size={16} />
                    </ChannelIcon>
                    <ChannelInfo>
                      <ChannelName>{channel.name || channel.channel_name}</ChannelName>
                      <ChannelMeta>@{channel.username || channel.channel_id}</ChannelMeta>
                    </ChannelInfo>
                    {isAssigned && <Check size={20} />}
                  </SelectableItem>
                );
              })
            )}
          </Modal>
        </ModalOverlay>
      )}

      {/* Instagram Modal */}
      {showInstagramModal && (
        <ModalOverlay onClick={() => setShowInstagramModal(false)}>
          <Modal onClick={e => e.stopPropagation()}>
            <ModalHeader>
              <ModalTitle>Выберите Instagram аккаунт</ModalTitle>
              <CloseButton onClick={() => setShowInstagramModal(false)}>
                <X size={20} />
              </CloseButton>
            </ModalHeader>

            {availableInstagramAccounts.length === 0 ? (
              <EmptyState>
                Нет доступных аккаунтов.<br />
                Добавьте аккаунт в разделе "Настройки → Instagram".
              </EmptyState>
            ) : (
              availableInstagramAccounts.map(account => {
                const isAssigned = account.project_id === parseInt(id);
                return (
                  <SelectableItem
                    key={account.id}
                    $selected={isAssigned}
                    onClick={() => !isAssigned && handleAssignInstagram(account.id)}
                    disabled={isAssigned}
                  >
                    <ChannelIcon $platform="instagram">
                      <Instagram size={16} />
                    </ChannelIcon>
                    <ChannelInfo>
                      <ChannelName>{account.name || account.username}</ChannelName>
                      <ChannelMeta>@{account.username}</ChannelMeta>
                    </ChannelInfo>
                    {isAssigned && <Check size={20} />}
                  </SelectableItem>
                );
              })
            )}
          </Modal>
        </ModalOverlay>
      )}
    </Container>
  );
};

export default ProjectSettings;


