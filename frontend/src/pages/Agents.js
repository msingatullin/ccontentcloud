import React from 'react';
import styled from 'styled-components';
import { useQuery } from 'react-query';
import { Bot, Activity, Settings, Play, Pause, RotateCcw } from 'lucide-react';
import { agentsAPI } from '../services/api';
import { AgentsOverview } from '../components/Dashboard/AgentsOverview';

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.xl};
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Title = styled.h1`
  font-size: ${props => props.theme.fontSize['3xl']};
  font-weight: ${props => props.theme.fontWeight.bold};
  color: ${props => props.theme.colors.text};
  margin: 0;
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
`;

const Actions = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.md};
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

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
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

const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: ${props => props.theme.spacing.xxxl};
  color: ${props => props.theme.colors.textSecondary};
`;

const ErrorContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: ${props => props.theme.spacing.xxxl};
  text-align: center;
  color: ${props => props.theme.colors.error};
`;

export const Agents = () => {
  const { 
    data: agentsData, 
    isLoading, 
    error, 
    refetch 
  } = useQuery('agentsStatus', agentsAPI.getAgentsStatus, {
    refetchInterval: 30000,
    staleTime: 10000,
  });

  const handleRefresh = () => {
    refetch();
  };

  const handleRestartAll = () => {
    // TODO: Implement restart all agents
    console.log('Restart all agents');
  };

  if (isLoading) {
    return (
      <LoadingContainer>
        <Activity className="animate-pulse" size={32} />
        <span style={{ marginLeft: '12px' }}>Загрузка агентов...</span>
      </LoadingContainer>
    );
  }

  if (error) {
    return (
      <ErrorContainer>
        <Bot size={48} style={{ marginBottom: '16px' }} />
        <h2>Ошибка загрузки агентов</h2>
        <p>Не удалось подключиться к API. Проверьте подключение к интернету.</p>
        <Button onClick={handleRefresh} style={{ marginTop: '16px' }}>
          <RotateCcw size={16} />
          Попробовать снова
        </Button>
      </ErrorContainer>
    );
  }

  return (
    <Container>
      <Header>
        <Title>
          <Bot size={32} />
          Управление агентами
        </Title>
        
        <Actions>
          <SecondaryButton onClick={handleRefresh}>
            <RotateCcw size={16} />
            Обновить
          </SecondaryButton>
          <Button onClick={handleRestartAll}>
            <Play size={16} />
            Перезапустить всех
          </Button>
        </Actions>
      </Header>

      <AgentsOverview agents={agentsData} />
    </Container>
  );
};
