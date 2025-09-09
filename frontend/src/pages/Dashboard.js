import React from 'react';
import styled from 'styled-components';
import { useQuery } from 'react-query';
import { 
  Activity, 
  Bot, 
  FileText, 
  TrendingUp, 
  Clock, 
  CheckCircle,
  AlertCircle,
  Zap
} from 'lucide-react';
import { agentsAPI, systemAPI } from '../services/api';
import { StatsCard } from '../components/Dashboard/StatsCard';
import { AgentsOverview } from '../components/Dashboard/AgentsOverview';
import { RecentActivity } from '../components/Dashboard/RecentActivity';
import { SystemStatus } from '../components/Dashboard/SystemStatus';

const DashboardContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.xl};
`;

const Header = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.md};
`;

const Title = styled.h1`
  font-size: ${props => props.theme.fontSize['3xl']};
  font-weight: ${props => props.theme.fontWeight.bold};
  color: ${props => props.theme.colors.text};
  margin: 0;
`;

const Subtitle = styled.p`
  font-size: ${props => props.theme.fontSize.lg};
  color: ${props => props.theme.colors.textSecondary};
  margin: 0;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: ${props => props.theme.spacing.lg};
`;

const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: ${props => props.theme.spacing.xl};

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
`;

const LeftColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.xl};
`;

const RightColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.xl};
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

const ErrorIcon = styled(AlertCircle)`
  width: 48px;
  height: 48px;
  margin-bottom: ${props => props.theme.spacing.md};
`;

export const Dashboard = () => {
  // Загружаем данные агентов
  const { 
    data: agentsData, 
    isLoading: agentsLoading, 
    error: agentsError 
  } = useQuery('agentsStatus', agentsAPI.getAgentsStatus, {
    refetchInterval: 30000, // Обновляем каждые 30 секунд
    staleTime: 10000, // Данные считаются устаревшими через 10 секунд
  });

  // Загружаем статус системы
  const { 
    data: systemData, 
    isLoading: systemLoading, 
    error: systemError 
  } = useQuery('systemStatus', systemAPI.getSystemStatus, {
    refetchInterval: 60000, // Обновляем каждую минуту
    staleTime: 30000,
  });

  // Вычисляем статистику
  const stats = React.useMemo(() => {
    if (!agentsData) return null;

    const agents = Object.values(agentsData);
    const totalAgents = agents.length;
    const activeAgents = agents.filter(agent => agent.status === 'idle' || agent.status === 'busy').length;
    const busyAgents = agents.filter(agent => agent.status === 'busy').length;
    const totalTasks = agents.reduce((sum, agent) => sum + agent.completed_tasks, 0);
    const totalErrors = agents.reduce((sum, agent) => sum + agent.error_count, 0);

    return {
      totalAgents,
      activeAgents,
      busyAgents,
      totalTasks,
      totalErrors,
      successRate: totalTasks > 0 ? ((totalTasks - totalErrors) / totalTasks * 100).toFixed(1) : 100
    };
  }, [agentsData]);

  if (agentsLoading || systemLoading) {
    return (
      <LoadingContainer>
        <Activity className="animate-pulse" size={32} />
        <span style={{ marginLeft: '12px' }}>Загрузка данных...</span>
      </LoadingContainer>
    );
  }

  if (agentsError || systemError) {
    return (
      <ErrorContainer>
        <ErrorIcon />
        <h2>Ошибка загрузки данных</h2>
        <p>Не удалось подключиться к API. Проверьте подключение к интернету.</p>
      </ErrorContainer>
    );
  }

  return (
    <DashboardContainer>
      <Header>
        <Title>Dashboard</Title>
        <Subtitle>
          Обзор системы AI Content Orchestrator
        </Subtitle>
      </Header>

      {stats && (
        <StatsGrid>
          <StatsCard
            title="Всего агентов"
            value={stats.totalAgents}
            icon={Bot}
            color="primary"
            trend={null}
          />
          <StatsCard
            title="Активных агентов"
            value={stats.activeAgents}
            icon={Activity}
            color="success"
            trend={null}
          />
          <StatsCard
            title="Выполнено задач"
            value={stats.totalTasks}
            icon={CheckCircle}
            color="info"
            trend={null}
          />
          <StatsCard
            title="Успешность"
            value={`${stats.successRate}%`}
            icon={TrendingUp}
            color="success"
            trend={null}
          />
        </StatsGrid>
      )}

      <ContentGrid>
        <LeftColumn>
          <AgentsOverview agents={agentsData} />
          <RecentActivity />
        </LeftColumn>
        
        <RightColumn>
          <SystemStatus systemData={systemData} />
        </RightColumn>
      </ContentGrid>
    </DashboardContainer>
  );
};
