import React from 'react';
import styled from 'styled-components';
import { 
  Server, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Activity,
  Database,
  Cpu,
  HardDrive
} from 'lucide-react';

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

const StatusList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.md};
`;

const StatusItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
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

const StatusInfo = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
`;

const StatusIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: ${props => props.theme.borderRadius.md};
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => {
    switch (props.status) {
      case 'healthy': return props.theme.colors.successLight;
      case 'warning': return props.theme.colors.warningLight;
      case 'error': return props.theme.colors.errorLight;
      default: return props.theme.colors.backgroundTertiary;
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'healthy': return props.theme.colors.success;
      case 'warning': return props.theme.colors.warning;
      case 'error': return props.theme.colors.error;
      default: return props.theme.colors.textSecondary;
    }
  }};
`;

const StatusDetails = styled.div`
  display: flex;
  flex-direction: column;
`;

const StatusName = styled.h3`
  font-size: ${props => props.theme.fontSize.base};
  font-weight: ${props => props.theme.fontWeight.medium};
  color: ${props => props.theme.colors.text};
  margin: 0 0 ${props => props.theme.spacing.xs} 0;
`;

const StatusDescription = styled.p`
  font-size: ${props => props.theme.fontSize.sm};
  color: ${props => props.theme.colors.textSecondary};
  margin: 0;
`;

const StatusValue = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  font-size: ${props => props.theme.fontSize.sm};
  font-weight: ${props => props.theme.fontWeight.medium};
  color: ${props => {
    switch (props.status) {
      case 'healthy': return props.theme.colors.success;
      case 'warning': return props.theme.colors.warning;
      case 'error': return props.theme.colors.error;
      default: return props.theme.colors.textSecondary;
    }
  }};
`;

const StatusIndicator = styled.div`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${props => {
    switch (props.status) {
      case 'healthy': return props.theme.colors.success;
      case 'warning': return props.theme.colors.warning;
      case 'error': return props.theme.colors.error;
      default: return props.theme.colors.textTertiary;
    }
  }};
`;

const getStatusIcon = (component) => {
  switch (component) {
    case 'api': return <Server size={20} />;
    case 'database': return <Database size={20} />;
    case 'cpu': return <Cpu size={20} />;
    case 'memory': return <HardDrive size={20} />;
    default: return <Activity size={20} />;
  }
};

const getStatusText = (status) => {
  switch (status) {
    case 'healthy': return 'Работает';
    case 'warning': return 'Предупреждение';
    case 'error': return 'Ошибка';
    default: return 'Неизвестно';
  }
};

export const SystemStatus = ({ systemData }) => {
  // Моковые данные для демонстрации
  const systemComponents = [
    {
      id: 'api',
      name: 'API Сервер',
      description: 'Основной API сервис',
      status: 'healthy',
      value: 'Online',
      icon: Server
    },
    {
      id: 'database',
      name: 'База данных',
      description: 'Хранилище данных',
      status: 'healthy',
      value: 'Connected',
      icon: Database
    },
    {
      id: 'cpu',
      name: 'CPU',
      description: 'Использование процессора',
      status: 'healthy',
      value: '45%',
      icon: Cpu
    },
    {
      id: 'memory',
      name: 'Память',
      description: 'Использование памяти',
      status: 'warning',
      value: '78%',
      icon: HardDrive
    }
  ];

  return (
    <Container>
      <Header>
        <Server size={24} />
        <Title>Статус системы</Title>
      </Header>

      <StatusList>
        {systemComponents.map((component) => (
          <StatusItem key={component.id}>
            <StatusInfo>
              <StatusIcon status={component.status}>
                {getStatusIcon(component.id)}
              </StatusIcon>
              <StatusDetails>
                <StatusName>{component.name}</StatusName>
                <StatusDescription>{component.description}</StatusDescription>
              </StatusDetails>
            </StatusInfo>
            
            <StatusValue status={component.status}>
              <StatusIndicator status={component.status} />
              {component.value}
            </StatusValue>
          </StatusItem>
        ))}
      </StatusList>
    </Container>
  );
};
