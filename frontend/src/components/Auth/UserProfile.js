/**
 * UserProfile - Компонент профиля пользователя
 */

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { User, Mail, Phone, Building, MapPin, Globe, Bell, Shield, Save, Eye, EyeOff } from 'lucide-react';
import styled from 'styled-components';
import { useAuth } from '../../contexts/AuthContext';

const ProfileContainer = styled.div`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
`;

const ProfileHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
`;

const Avatar = styled.div`
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #06b6d4, #10b981);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  font-weight: 700;
`;

const UserInfo = styled.div`
  flex: 1;
`;

const UserName = styled.h2`
  color: #e2e8f0;
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px 0;
`;

const UserEmail = styled.p`
  color: #94a3b8;
  font-size: 14px;
  margin: 0;
`;

const UserRole = styled.span`
  display: inline-block;
  background: linear-gradient(135deg, #06b6d4, #10b981);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  margin-top: 8px;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const FormSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const SectionTitle = styled.h3`
  color: #e2e8f0;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const FormRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const FormGroup = styled.div`
  position: relative;
`;

const Label = styled.label`
  display: block;
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
`;

const InputContainer = styled.div`
  position: relative;
`;

const Input = styled.input`
  width: 100%;
  padding: 12px 16px 12px 44px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid ${props => props.error ? '#ef4444' : 'rgba(255, 255, 255, 0.1)'};
  border-radius: 12px;
  color: #e2e8f0;
  font-size: 16px;
  transition: all 0.3s ease;
  
  &:focus {
    outline: none;
    border-color: #06b6d4;
    box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
  }
  
  &::placeholder {
    color: #64748b;
  }
`;

const InputIcon = styled.div`
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  z-index: 1;
`;

const PasswordToggle = styled.button`
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: color 0.3s ease;
  
  &:hover {
    color: #06b6d4;
  }
`;

const ErrorMessage = styled.span`
  color: #ef4444;
  font-size: 12px;
  margin-top: 4px;
  display: block;
`;

const SaveButton = styled.button`
  background: linear-gradient(135deg, #06b6d4, #10b981);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  padding: 14px 28px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  align-self: flex-start;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(6, 182, 212, 0.3);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
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

const Switch = styled.label`
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
`;

const SwitchInput = styled.input`
  display: none;
`;

const SwitchSlider = styled.div`
  width: 48px;
  height: 24px;
  background: ${props => props.checked ? '#06b6d4' : 'rgba(255, 255, 255, 0.2)'};
  border-radius: 24px;
  position: relative;
  transition: background 0.3s ease;
  
  &::before {
    content: '';
    position: absolute;
    top: 2px;
    left: ${props => props.checked ? '26px' : '2px'};
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    transition: left 0.3s ease;
  }
`;

const SwitchLabel = styled.span`
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 500;
`;

function UserProfile() {
  const { user, updateProfile, changePassword } = useAuth();
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  
  const {
    register: registerProfile,
    handleSubmit: handleProfileSubmit,
    formState: { errors: profileErrors },
    reset: resetProfile
  } = useForm({
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      phone: user?.phone || '',
      company: user?.company || '',
      position: user?.position || '',
      timezone: user?.timezone || 'Europe/Moscow',
      language: user?.language || 'ru',
      notifications_enabled: user?.notifications_enabled ?? true,
      marketing_emails: user?.marketing_emails ?? false
    }
  });

  const {
    register: registerPassword,
    handleSubmit: handlePasswordSubmit,
    formState: { errors: passwordErrors },
    reset: resetPassword,
    watch
  } = useForm();

  const newPassword = watch('new_password');

  const onProfileSubmit = async (data) => {
    try {
      setIsUpdatingProfile(true);
      const result = await updateProfile(data);
      
      if (result.success) {
        resetProfile(data);
      }
    } catch (error) {
      console.error('Error updating profile:', error);
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const onPasswordSubmit = async (data) => {
    try {
      setIsChangingPassword(true);
      const result = await changePassword(data.current_password, data.new_password);
      
      if (result.success) {
        resetPassword();
      }
    } catch (error) {
      console.error('Error changing password:', error);
    } finally {
      setIsChangingPassword(false);
    }
  };

  const getInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    if (user?.username) {
      return user.username[0].toUpperCase();
    }
    return 'U';
  };

  const getRoleLabel = (role) => {
    switch (role) {
      case 'admin': return 'Администратор';
      case 'moderator': return 'Модератор';
      default: return 'Пользователь';
    }
  };

  return (
    <ProfileContainer>
      <ProfileHeader>
        <Avatar>{getInitials()}</Avatar>
        <UserInfo>
          <UserName>{user?.get_display_name || user?.username}</UserName>
          <UserEmail>{user?.email}</UserEmail>
          <UserRole>{getRoleLabel(user?.role)}</UserRole>
        </UserInfo>
      </ProfileHeader>

      <Form onSubmit={handleProfileSubmit(onProfileSubmit)}>
        <FormSection>
          <SectionTitle>
            <User size={20} />
            Личная информация
          </SectionTitle>
          
          <FormRow>
            <FormGroup>
              <Label>Имя</Label>
              <InputContainer>
                <InputIcon>
                  <User size={20} />
                </InputIcon>
                <Input
                  type="text"
                  placeholder="Введите ваше имя"
                  error={profileErrors.first_name}
                  {...registerProfile('first_name')}
                />
              </InputContainer>
              {profileErrors.first_name && (
                <ErrorMessage>{profileErrors.first_name.message}</ErrorMessage>
              )}
            </FormGroup>

            <FormGroup>
              <Label>Фамилия</Label>
              <InputContainer>
                <InputIcon>
                  <User size={20} />
                </InputIcon>
                <Input
                  type="text"
                  placeholder="Введите вашу фамилию"
                  error={profileErrors.last_name}
                  {...registerProfile('last_name')}
                />
              </InputContainer>
              {profileErrors.last_name && (
                <ErrorMessage>{profileErrors.last_name.message}</ErrorMessage>
              )}
            </FormGroup>
          </FormRow>

          <FormRow>
            <FormGroup>
              <Label>Телефон</Label>
              <InputContainer>
                <InputIcon>
                  <Phone size={20} />
                </InputIcon>
                <Input
                  type="tel"
                  placeholder="+7 (999) 123-45-67"
                  error={profileErrors.phone}
                  {...registerProfile('phone')}
                />
              </InputContainer>
              {profileErrors.phone && (
                <ErrorMessage>{profileErrors.phone.message}</ErrorMessage>
              )}
            </FormGroup>

            <FormGroup>
              <Label>Компания</Label>
              <InputContainer>
                <InputIcon>
                  <Building size={20} />
                </InputIcon>
                <Input
                  type="text"
                  placeholder="Название компании"
                  error={profileErrors.company}
                  {...registerProfile('company')}
                />
              </InputContainer>
            </FormGroup>
          </FormRow>

          <FormGroup>
            <Label>Должность</Label>
            <InputContainer>
              <InputIcon>
                <User size={20} />
              </InputIcon>
              <Input
                type="text"
                placeholder="Ваша должность"
                error={profileErrors.position}
                {...registerProfile('position')}
              />
            </InputContainer>
          </FormGroup>
        </FormSection>

        <FormSection>
          <SectionTitle>
            <Globe size={20} />
            Настройки
          </SectionTitle>
          
          <FormRow>
            <FormGroup>
              <Label>Часовой пояс</Label>
              <InputContainer>
                <InputIcon>
                  <MapPin size={20} />
                </InputIcon>
                <Input
                  type="text"
                  placeholder="Europe/Moscow"
                  error={profileErrors.timezone}
                  {...registerProfile('timezone')}
                />
              </InputContainer>
            </FormGroup>

            <FormGroup>
              <Label>Язык</Label>
              <InputContainer>
                <InputIcon>
                  <Globe size={20} />
                </InputIcon>
                <Input
                  type="text"
                  placeholder="ru"
                  error={profileErrors.language}
                  {...registerProfile('language')}
                />
              </InputContainer>
            </FormGroup>
          </FormRow>

          <FormGroup>
            <Switch>
              <SwitchInput
                type="checkbox"
                {...registerProfile('notifications_enabled')}
              />
              <SwitchSlider />
              <SwitchLabel>Уведомления включены</SwitchLabel>
            </Switch>
          </FormGroup>

          <FormGroup>
            <Switch>
              <SwitchInput
                type="checkbox"
                {...registerProfile('marketing_emails')}
              />
              <SwitchSlider />
              <SwitchLabel>Маркетинговые рассылки</SwitchLabel>
            </Switch>
          </FormGroup>
        </FormSection>

        <SaveButton type="submit" disabled={isUpdatingProfile}>
          {isUpdatingProfile ? (
            <LoadingSpinner />
          ) : (
            <>
              <Save size={20} />
              Сохранить изменения
            </>
          )}
        </SaveButton>
      </Form>

      <Form onSubmit={handlePasswordSubmit(onPasswordSubmit)} style={{ marginTop: '32px' }}>
        <FormSection>
          <SectionTitle>
            <Shield size={20} />
            Безопасность
          </SectionTitle>
          
          <FormGroup>
            <Label>Текущий пароль</Label>
            <InputContainer>
              <InputIcon>
                <Shield size={20} />
              </InputIcon>
              <Input
                type={showCurrentPassword ? 'text' : 'password'}
                placeholder="Введите текущий пароль"
                error={passwordErrors.current_password}
                {...registerPassword('current_password', {
                  required: 'Текущий пароль обязателен'
                })}
              />
              <PasswordToggle
                type="button"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
              >
                {showCurrentPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </PasswordToggle>
            </InputContainer>
            {passwordErrors.current_password && (
              <ErrorMessage>{passwordErrors.current_password.message}</ErrorMessage>
            )}
          </FormGroup>

          <FormRow>
            <FormGroup>
              <Label>Новый пароль</Label>
              <InputContainer>
                <InputIcon>
                  <Shield size={20} />
                </InputIcon>
                <Input
                  type={showNewPassword ? 'text' : 'password'}
                  placeholder="Введите новый пароль"
                  error={passwordErrors.new_password}
                  {...registerPassword('new_password', {
                    required: 'Новый пароль обязателен',
                    minLength: {
                      value: 8,
                      message: 'Пароль должен содержать минимум 8 символов'
                    }
                  })}
                />
                <PasswordToggle
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                >
                  {showNewPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </PasswordToggle>
              </InputContainer>
              {passwordErrors.new_password && (
                <ErrorMessage>{passwordErrors.new_password.message}</ErrorMessage>
              )}
            </FormGroup>

            <FormGroup>
              <Label>Подтверждение пароля</Label>
              <InputContainer>
                <InputIcon>
                  <Shield size={20} />
                </InputIcon>
                <Input
                  type="password"
                  placeholder="Подтвердите новый пароль"
                  error={passwordErrors.confirm_password}
                  {...registerPassword('confirm_password', {
                    required: 'Подтверждение пароля обязательно',
                    validate: value => value === newPassword || 'Пароли не совпадают'
                  })}
                />
              </InputContainer>
              {passwordErrors.confirm_password && (
                <ErrorMessage>{passwordErrors.confirm_password.message}</ErrorMessage>
              )}
            </FormGroup>
          </FormRow>

          <SaveButton type="submit" disabled={isChangingPassword}>
            {isChangingPassword ? (
              <LoadingSpinner />
            ) : (
              <>
                <Shield size={20} />
                Изменить пароль
              </>
            )}
          </SaveButton>
        </FormSection>
      </Form>
    </ProfileContainer>
  );
}

export default UserProfile;
