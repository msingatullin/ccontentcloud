import React from 'react';
import styled from 'styled-components';
import { Bot, Activity, CheckCircle, AlertCircle, Clock } from 'lucide-react';

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
  justify-content: space-between;
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const Title = styled.h2`
  font-size: ${props => props.theme.fontSize.xl};
  font-weight: ${props => props.theme.fontWeight.semibold};
  color: ${props => props.theme.colors.text};
  margin: 0;
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
`;

const AgentsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: ${props => props.theme.spacing.md};
`;

const AgentCard = styled.div`
  background: ${props => props.theme.colors.background};
  border: 1px solid ${props => props.theme.colors.borderLight};
  border-radius: ${props => props.theme.borderRadius.md};
  padding: ${props => props.theme.spacing.md};
  transition: all ${props => props.theme.transitions.normal};

  &:hover {
    border-color: ${props => props.theme.colors.primary};
    box-shadow: ${props => props.theme.colors.shadowMd};
  }
`;

const AgentHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${props => props.theme.spacing.sm};
`;

const AgentName = styled.h3`
  font-size: ${props => props.theme.fontSize.base};
  font-weight: ${props => props.theme.fontWeight.medium};
  color: ${props => props.theme.colors.text};
  margin: 0;
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
`;

const StatusBadge = styled.span`
  padding: ${props => props.theme.spacing.xs} ${props => props.theme.spacing.sm};
  border-radius: ${props => props.theme.borderRadius.full};
  font-size: ${props => props.theme.fontSize.xs};
  font-weight: ${props => props.theme.fontWeight.medium};
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: ${props => {
    switch (props.status) {
      case 'idle': return props.theme.colors.successLight;
      case 'busy': return props.theme.colors.warningLight;
      case 'error': return props.theme.colors.errorLight;
      default: return props.theme.colors.backgroundTertiary;
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'idle': return props.theme.colors.success;
      case 'busy': return props.theme.colors.warning;
      case 'error': return props.theme.colors.error;
      default: return props.theme.colors.textSecondary;
    }
  }};
`;

const AgentStats = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: ${props => props.theme.spacing.sm};
  margin-top: ${props => props.theme.spacing.sm};
`;

const StatItem = styled.div`
  text-align: center;
`;

const StatValue = styled.div`
  font-size: ${props => props.theme.fontSize.lg};
  font-weight: ${props => props.theme.fontWeight.semibold};
  color: ${props => props.theme.colors.text};
`;

const StatLabel = styled.div`
  font-size: ${props => props.theme.fontSize.xs};
  color: ${props => props.theme.colors.textSecondary};
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const Specializations = styled.div`
  margin-top: ${props => props.theme.spacing.sm};
`;

const SpecializationTag = styled.span`
  display: inline-block;
  padding: 2px 6px;
  margin: 2px;
  background: ${props => props.theme.colors.backgroundTertiary};
  color: ${props => props.theme.colors.textSecondary};
  border-radius: ${props => props.theme.borderRadius.sm};
  font-size: ${props => props.theme.fontSize.xs};
`;

const getStatusIcon = (status) => {
  switch (status) {
    case 'idle': return <CheckCircle size={16} />;
    case 'busy': return <Activity size={16} />;
    case 'error': return <AlertCircle size={16} />;
    default: return <Clock size={16} />;
  }
};

const getStatusText = (status) => {
  switch (status) {
    case 'idle': return 'Готов';
    case 'busy': return 'Работает';
    case 'error': return 'Ошибка';
    default: return 'Неизвестно';
  }
};

export const AgentsOverview = ({ agents }) => {
  if (!agents) {
    return (
      <Container>
        <Header>
          <Title>
            <Bot size={24} />
            Обзор агентов
          </Title>
        </Header>
        <div>Загрузка данных агентов...</div>
      </Container>
    );
  }

  const agentsList = Object.values(agents);

  return (
    <Container>
      <Header>
        <Title>
          <Bot size={24} />
          Обзор агентов
        </Title>
      </Header>

      <AgentsGrid>
        {agentsList.map((agent) => (
          <AgentCard key={agent.agent_id}>
            <AgentHeader>
              <AgentName>
                <Bot size={16} />
                {agent.name}
              </AgentName>
              <StatusBadge status={agent.status}>
                {getStatusIcon(agent.status)}
                {getStatusText(agent.status)}
              </StatusBadge>
            </AgentHeader>

            <AgentStats>
              <StatItem>
                <StatValue>{agent.completed_tasks}</StatValue>
                <StatLabel>Задач</StatLabel>
              </StatItem>
              <StatItem>
                <StatValue>{agent.current_tasks}</StatValue>
                <StatLabel>Активных</StatLabel>
              </StatItem>
              <StatItem>
                <StatValue>{agent.error_count}</StatValue>
                <StatLabel>Ошибок</StatLabel>
              </StatItem>
            </AgentStats>

            <Specializations>
              {agent.capabilities?.specializations?.slice(0, 3).map((spec, index) => (
                <SpecializationTag key={index}>
                  {spec}
                </SpecializationTag>
              ))}
              {agent.capabilities?.specializations?.length > 3 && (
                <SpecializationTag>
                  +{agent.capabilities.specializations.length - 3}
                </SpecializationTag>
              )}
            </Specializations>
          </AgentCard>
        ))}
      </AgentsGrid>
    </Container>
  );
};
