import React from 'react';
import styled from 'styled-components';
import { 
  Activity, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Bot,
  FileText,
  Zap
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';

const Container = styled.div`
  background: ${props => props.theme.colors.backgroundSecondary};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.lg};
  padding: ${props => props.theme.spacing.lg};
  box-shadow: ${props => props.theme.colors.shadow};
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const Title = styled.h2`
  font-size: ${props => props.theme.fontSize.xl};
  font-weight: ${props => props.theme.fontWeight.semibold};
  color: ${props => props.theme.colors.text};
  margin: 0;
`;

const ActivityList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.md};
`;

const ActivityItem = styled.div`
  display: flex;
  align-items: flex-start;
  gap: ${props => props.theme.spacing.md};
  padding: ${props => props.theme.spacing.md};
  background: ${props => props.theme.colors.background};
  border: 1px solid ${props => props.theme.colors.borderLight};
  border-radius: ${props => props.theme.borderRadius.md};
  transition: all ${props => props.theme.transitions.normal};

  &:hover {
    border-color: ${props => props.theme.colors.primary};
    box-shadow: ${props => props.theme.colors.shadow};
  }
`;

const ActivityIcon = styled.div`
  width: 32px;
  height: 32px;
  border-radius: ${props => props.theme.borderRadius.md};
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => {
    switch (props.type) {
      case 'success': return props.theme.colors.successLight;
      case 'warning': return props.theme.colors.warningLight;
      case 'error': return props.theme.colors.errorLight;
      case 'info': return props.theme.colors.infoLight;
      default: return props.theme.colors.backgroundTertiary;
    }
  }};
  color: ${props => {
    switch (props.type) {
      case 'success': return props.theme.colors.success;
      case 'warning': return props.theme.colors.warning;
      case 'error': return props.theme.colors.error;
      case 'info': return props.theme.colors.info;
      default: return props.theme.colors.textSecondary;
    }
  }};
  flex-shrink: 0;
`;

const ActivityContent = styled.div`
  flex: 1;
  min-width: 0;
`;

const ActivityTitle = styled.h3`
  font-size: ${props => props.theme.fontSize.sm};
  font-weight: ${props => props.theme.fontWeight.medium};
  color: ${props => props.theme.colors.text};
  margin: 0 0 ${props => props.theme.spacing.xs} 0;
`;

const ActivityDescription = styled.p`
  font-size: ${props => props.theme.fontSize.sm};
  color: ${props => props.theme.colors.textSecondary};
  margin: 0 0 ${props => props.theme.spacing.xs} 0;
`;

const ActivityTime = styled.span`
  font-size: ${props => props.theme.fontSize.xs};
  color: ${props => props.theme.colors.textTertiary};
`;

const EmptyState = styled.div`
  text-align: center;
  padding: ${props => props.theme.spacing.xl};
  color: ${props => props.theme.colors.textSecondary};
`;

const getActivityIcon = (type) => {
  switch (type) {
    case 'success': return <CheckCircle size={16} />;
    case 'warning': return <AlertCircle size={16} />;
    case 'error': return <AlertCircle size={16} />;
    case 'info': return <Activity size={16} />;
    default: return <Clock size={16} />;
  }
};

export const RecentActivity = () => {
  // Моковые данные для демонстрации
  const activities = [
    {
      id: 1,
      type: 'success',
      title: 'Задача выполнена',
      description: 'Chief Content Agent завершил создание контента',
      timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 минут назад
      agent: 'Chief Content Agent'
    },
    {
      id: 2,
      type: 'info',
      title: 'Новая задача',
      description: 'Multimedia Producer Agent начал генерацию изображения',
      timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 минут назад
      agent: 'Multimedia Producer Agent'
    },
    {
      id: 3,
      type: 'success',
      title: 'Контент опубликован',
      description: 'Publisher Agent успешно опубликовал материал',
      timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 минут назад
      agent: 'Publisher Agent'
    },
    {
      id: 4,
      type: 'warning',
      title: 'Предупреждение',
      description: 'Legal Guard Agent обнаружил потенциальные риски',
      timestamp: new Date(Date.now() - 45 * 60 * 1000), // 45 минут назад
      agent: 'Legal Guard Agent'
    },
    {
      id: 5,
      type: 'info',
      title: 'A/B тест запущен',
      description: 'Paid Creative Agent начал тестирование креативов',
      timestamp: new Date(Date.now() - 60 * 60 * 1000), // 1 час назад
      agent: 'Paid Creative Agent'
    }
  ];

  if (activities.length === 0) {
    return (
      <Container>
        <Header>
          <Activity size={24} />
          <Title>Последняя активность</Title>
        </Header>
        <EmptyState>
          <Activity size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
          <p>Нет недавней активности</p>
        </EmptyState>
      </Container>
    );
  }

  return (
    <Container>
      <Header>
        <Activity size={24} />
        <Title>Последняя активность</Title>
      </Header>

      <ActivityList>
        {activities.map((activity) => (
          <ActivityItem key={activity.id}>
            <ActivityIcon type={activity.type}>
              {getActivityIcon(activity.type)}
            </ActivityIcon>
            
            <ActivityContent>
              <ActivityTitle>{activity.title}</ActivityTitle>
              <ActivityDescription>{activity.description}</ActivityDescription>
              <ActivityTime>
                {formatDistanceToNow(activity.timestamp, { 
                  addSuffix: true, 
                  locale: ru 
                })}
              </ActivityTime>
            </ActivityContent>
          </ActivityItem>
        ))}
      </ActivityList>
    </Container>
  );
};
