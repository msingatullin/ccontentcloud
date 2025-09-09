import React, { useState } from 'react';
import styled from 'styled-components';
import { 
  Settings as SettingsIcon, 
  Save, 
  RotateCcw, 
  Database,
  Bell,
  Shield,
  Palette,
  Globe
} from 'lucide-react';

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

const Title = styled.h1`
  font-size: ${props => props.theme.fontSize['3xl']};
  font-weight: ${props => props.theme.fontWeight.bold};
  color: ${props => props.theme.colors.text};
  margin: 0;
`;

const SettingsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: ${props => props.theme.spacing.xl};
`;

const SettingsSection = styled.div`
  background: ${props => props.theme.colors.backgroundSecondary};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.lg};
  padding: ${props => props.theme.spacing.lg};
  box-shadow: ${props => props.theme.colors.shadow};
`;

const SectionHeader = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
  margin-bottom: ${props => props.theme.spacing.lg};
  padding-bottom: ${props => props.theme.spacing.md};
  border-bottom: 1px solid ${props => props.theme.colors.border};
`;

const SectionTitle = styled.h2`
  font-size: ${props => props.theme.fontSize.xl};
  font-weight: ${props => props.theme.fontWeight.semibold};
  color: ${props => props.theme.colors.text};
  margin: 0;
`;

const SettingItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${props => props.theme.spacing.md} 0;
  border-bottom: 1px solid ${props => props.theme.colors.borderLight};

  &:last-child {
    border-bottom: none;
  }
`;

const SettingInfo = styled.div`
  flex: 1;
`;

const SettingLabel = styled.h3`
  font-size: ${props => props.theme.fontSize.base};
  font-weight: ${props => props.theme.fontWeight.medium};
  color: ${props => props.theme.colors.text};
  margin: 0 0 ${props => props.theme.spacing.xs} 0;
`;

const SettingDescription = styled.p`
  font-size: ${props => props.theme.fontSize.sm};
  color: ${props => props.theme.colors.textSecondary};
  margin: 0;
`;

const Toggle = styled.label`
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
`;

const ToggleInput = styled.input`
  opacity: 0;
  width: 0;
  height: 0;

  &:checked + span {
    background-color: ${props => props.theme.colors.primary};
  }

  &:checked + span:before {
    transform: translateX(24px);
  }
`;

const ToggleSlider = styled.span`
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: ${props => props.theme.colors.border};
  transition: 0.3s;
  border-radius: 24px;

  &:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: 0.3s;
    border-radius: 50%;
  }
`;

const Select = styled.select`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  background: ${props => props.theme.colors.background};
  color: ${props => props.theme.colors.text};
  font-size: ${props => props.theme.fontSize.sm};

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const Input = styled.input`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  background: ${props => props.theme.colors.background};
  color: ${props => props.theme.colors.text};
  font-size: ${props => props.theme.fontSize.sm};
  width: 200px;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
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

  &:hover {
    background: ${props => props.theme.colors.primaryHover};
    transform: translateY(-1px);
  }
`;

const SecondaryButton = styled(Button)`
  background: ${props => props.theme.colors.backgroundSecondary};
  color: ${props => props.theme.colors.text};
  border: 1px solid ${props => props.theme.colors.border};

  &:hover {
    background: ${props => props.theme.colors.backgroundTertiary};
    border-color: ${props => props.theme.colors.primary};
  }
`;

const Actions = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.md};
  justify-content: flex-end;
  margin-top: ${props => props.theme.spacing.xl};
  padding-top: ${props => props.theme.spacing.lg};
  border-top: 1px solid ${props => props.theme.colors.border};
`;

export const Settings = () => {
  const [settings, setSettings] = useState({
    // Общие настройки
    autoSave: true,
    darkMode: false,
    language: 'ru',
    
    // Уведомления
    emailNotifications: true,
    pushNotifications: false,
    taskCompleted: true,
    systemAlerts: true,
    
    // Безопасность
    twoFactorAuth: false,
    sessionTimeout: 30,
    apiKeyRotation: true,
    
    // Производительность
    cacheEnabled: true,
    maxConcurrentTasks: 5,
    requestTimeout: 30
  });

  const handleToggle = (key) => {
    setSettings(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleInputChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSave = () => {
    // TODO: Save settings to API
    console.log('Saving settings:', settings);
  };

  const handleReset = () => {
    // TODO: Reset to default settings
    console.log('Resetting settings');
  };

  return (
    <Container>
      <Header>
        <SettingsIcon size={32} />
        <Title>Настройки системы</Title>
      </Header>

      <SettingsGrid>
        {/* Общие настройки */}
        <SettingsSection>
          <SectionHeader>
            <Globe size={24} />
            <SectionTitle>Общие настройки</SectionTitle>
          </SectionHeader>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Автосохранение</SettingLabel>
              <SettingDescription>Автоматически сохранять изменения</SettingDescription>
            </SettingInfo>
            <Toggle>
              <ToggleInput
                type="checkbox"
                checked={settings.autoSave}
                onChange={() => handleToggle('autoSave')}
              />
              <ToggleSlider />
            </Toggle>
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Темная тема</SettingLabel>
              <SettingDescription>Переключить на темную тему</SettingDescription>
            </SettingInfo>
            <Toggle>
              <ToggleInput
                type="checkbox"
                checked={settings.darkMode}
                onChange={() => handleToggle('darkMode')}
              />
              <ToggleSlider />
            </Toggle>
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Язык интерфейса</SettingLabel>
              <SettingDescription>Выберите язык интерфейса</SettingDescription>
            </SettingInfo>
            <Select
              value={settings.language}
              onChange={(e) => handleInputChange('language', e.target.value)}
            >
              <option value="ru">Русский</option>
              <option value="en">English</option>
            </Select>
          </SettingItem>
        </SettingsSection>

        {/* Уведомления */}
        <SettingsSection>
          <SectionHeader>
            <Bell size={24} />
            <SectionTitle>Уведомления</SectionTitle>
          </SectionHeader>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Email уведомления</SettingLabel>
              <SettingDescription>Получать уведомления на email</SettingDescription>
            </SettingInfo>
            <Toggle>
              <ToggleInput
                type="checkbox"
                checked={settings.emailNotifications}
                onChange={() => handleToggle('emailNotifications')}
              />
              <ToggleSlider />
            </Toggle>
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Push уведомления</SettingLabel>
              <SettingDescription>Получать push уведомления в браузере</SettingDescription>
            </SettingInfo>
            <Toggle>
              <ToggleInput
                type="checkbox"
                checked={settings.pushNotifications}
                onChange={() => handleToggle('pushNotifications')}
              />
              <ToggleSlider />
            </Toggle>
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Завершение задач</SettingLabel>
              <SettingDescription>Уведомлять о завершении задач</SettingDescription>
            </SettingInfo>
            <Toggle>
              <ToggleInput
                type="checkbox"
                checked={settings.taskCompleted}
                onChange={() => handleToggle('taskCompleted')}
              />
              <ToggleSlider />
            </Toggle>
          </SettingItem>
        </SettingsSection>

        {/* Безопасность */}
        <SettingsSection>
          <SectionHeader>
            <Shield size={24} />
            <SectionTitle>Безопасность</SectionTitle>
          </SectionHeader>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Двухфакторная аутентификация</SettingLabel>
              <SettingDescription>Дополнительная защита аккаунта</SettingDescription>
            </SettingInfo>
            <Toggle>
              <ToggleInput
                type="checkbox"
                checked={settings.twoFactorAuth}
                onChange={() => handleToggle('twoFactorAuth')}
              />
              <ToggleSlider />
            </Toggle>
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Таймаут сессии (минуты)</SettingLabel>
              <SettingDescription>Время неактивности до автоматического выхода</SettingDescription>
            </SettingInfo>
            <Input
              type="number"
              value={settings.sessionTimeout}
              onChange={(e) => handleInputChange('sessionTimeout', parseInt(e.target.value))}
              min="5"
              max="120"
            />
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Ротация API ключей</SettingLabel>
              <SettingDescription>Автоматическая смена API ключей</SettingDescription>
            </SettingInfo>
            <Toggle>
              <ToggleInput
                type="checkbox"
                checked={settings.apiKeyRotation}
                onChange={() => handleToggle('apiKeyRotation')}
              />
              <ToggleSlider />
            </Toggle>
          </SettingItem>
        </SettingsSection>

        {/* Производительность */}
        <SettingsSection>
          <SectionHeader>
            <Database size={24} />
            <SectionTitle>Производительность</SectionTitle>
          </SectionHeader>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Кэширование</SettingLabel>
              <SettingDescription>Включить кэширование данных</SettingDescription>
            </SettingInfo>
            <Toggle>
              <ToggleInput
                type="checkbox"
                checked={settings.cacheEnabled}
                onChange={() => handleToggle('cacheEnabled')}
              />
              <ToggleSlider />
            </Toggle>
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Максимум одновременных задач</SettingLabel>
              <SettingDescription>Количество задач, выполняемых одновременно</SettingDescription>
            </SettingInfo>
            <Input
              type="number"
              value={settings.maxConcurrentTasks}
              onChange={(e) => handleInputChange('maxConcurrentTasks', parseInt(e.target.value))}
              min="1"
              max="20"
            />
          </SettingItem>

          <SettingItem>
            <SettingInfo>
              <SettingLabel>Таймаут запросов (секунды)</SettingLabel>
              <SettingDescription>Максимальное время ожидания ответа</SettingDescription>
            </SettingInfo>
            <Input
              type="number"
              value={settings.requestTimeout}
              onChange={(e) => handleInputChange('requestTimeout', parseInt(e.target.value))}
              min="5"
              max="300"
            />
          </SettingItem>
        </SettingsSection>
      </SettingsGrid>

      <Actions>
        <SecondaryButton onClick={handleReset}>
          <RotateCcw size={16} />
          Сбросить
        </SecondaryButton>
        <Button onClick={handleSave}>
          <Save size={16} />
          Сохранить настройки
        </Button>
      </Actions>
    </Container>
  );
};
