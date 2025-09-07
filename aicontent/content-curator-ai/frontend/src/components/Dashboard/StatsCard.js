import React from 'react';
import styled from 'styled-components';
import { TrendingUp, TrendingDown } from 'lucide-react';

const Card = styled.div`
  background: ${props => props.theme.colors.backgroundSecondary};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.lg};
  padding: ${props => props.theme.spacing.lg};
  box-shadow: ${props => props.theme.colors.shadow};
  transition: all ${props => props.theme.transitions.normal};
  position: relative;
  overflow: hidden;

  &:hover {
    box-shadow: ${props => props.theme.colors.shadowMd};
    transform: translateY(-2px);
  }
`;

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${props => props.theme.spacing.md};
`;

const CardTitle = styled.h3`
  font-size: ${props => props.theme.fontSize.sm};
  font-weight: ${props => props.theme.fontWeight.medium};
  color: ${props => props.theme.colors.textSecondary};
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const IconContainer = styled.div`
  width: 40px;
  height: 40px;
  border-radius: ${props => props.theme.borderRadius.md};
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => {
    switch (props.color) {
      case 'primary': return props.theme.colors.primaryLight;
      case 'success': return props.theme.colors.successLight;
      case 'warning': return props.theme.colors.warningLight;
      case 'error': return props.theme.colors.errorLight;
      case 'info': return props.theme.colors.infoLight;
      default: return props.theme.colors.backgroundTertiary;
    }
  }};
  color: ${props => {
    switch (props.color) {
      case 'primary': return props.theme.colors.primary;
      case 'success': return props.theme.colors.success;
      case 'warning': return props.theme.colors.warning;
      case 'error': return props.theme.colors.error;
      case 'info': return props.theme.colors.info;
      default: return props.theme.colors.textSecondary;
    }
  }};
`;

const CardContent = styled.div`
  display: flex;
  align-items: baseline;
  gap: ${props => props.theme.spacing.sm};
`;

const CardValue = styled.div`
  font-size: ${props => props.theme.fontSize['3xl']};
  font-weight: ${props => props.theme.fontWeight.bold};
  color: ${props => props.theme.colors.text};
  line-height: 1;
`;

const TrendContainer = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.xs};
  font-size: ${props => props.theme.fontSize.sm};
  font-weight: ${props => props.theme.fontWeight.medium};
  color: ${props => {
    if (props.trend === null) return props.theme.colors.textTertiary;
    return props.trend > 0 ? props.theme.colors.success : props.theme.colors.error;
  }};
`;

const TrendIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
`;

const BackgroundPattern = styled.div`
  position: absolute;
  top: 0;
  right: 0;
  width: 100px;
  height: 100px;
  opacity: 0.05;
  background: ${props => {
    switch (props.color) {
      case 'primary': return props.theme.colors.primary;
      case 'success': return props.theme.colors.success;
      case 'warning': return props.theme.colors.warning;
      case 'error': return props.theme.colors.error;
      case 'info': return props.theme.colors.info;
      default: return props.theme.colors.textSecondary;
    }
  }};
  border-radius: 50%;
  transform: translate(30px, -30px);
`;

export const StatsCard = ({ 
  title, 
  value, 
  icon: Icon, 
  color = 'primary', 
  trend = null,
  trendValue = null,
  description = null 
}) => {
  return (
    <Card>
      <BackgroundPattern color={color} />
      
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <IconContainer color={color}>
          <Icon size={20} />
        </IconContainer>
      </CardHeader>

      <CardContent>
        <CardValue>{value}</CardValue>
        
        {trend !== null && (
          <TrendContainer trend={trend}>
            <TrendIcon>
              {trend > 0 ? (
                <TrendingUp size={16} />
              ) : (
                <TrendingDown size={16} />
              )}
            </TrendIcon>
            {trendValue && (
              <span>{Math.abs(trendValue)}%</span>
            )}
          </TrendContainer>
        )}
      </CardContent>

      {description && (
        <div style={{ 
          marginTop: '8px', 
          fontSize: '12px', 
          color: '#64748b' 
        }}>
          {description}
        </div>
      )}
    </Card>
  );
};
