import React, { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { 
  LayoutDashboard, 
  Bot, 
  FileText, 
  Settings, 
  Menu, 
  X,
  Activity,
  Zap,
  User,
  LogOut,
  Bell
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const NavigationContainer = styled.nav`
  position: fixed;
  top: 0;
  left: 0;
  width: 280px;
  height: 100vh;
  background: ${props => props.theme.colors.backgroundSecondary};
  border-right: 1px solid ${props => props.theme.colors.border};
  display: flex;
  flex-direction: column;
  z-index: ${props => props.theme.zIndex.fixed};
  transition: transform 0.3s ease;

  @media (max-width: 768px) {
    transform: ${props => props.isOpen ? 'translateX(0)' : 'translateX(-100%)'};
  }
`;

const Header = styled.div`
  padding: ${props => props.theme.spacing.lg};
  border-bottom: 1px solid ${props => props.theme.colors.border};
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  font-size: ${props => props.theme.fontSize.lg};
  font-weight: ${props => props.theme.fontWeight.bold};
  color: ${props => props.theme.colors.text};
`;

const LogoIcon = styled.div`
  width: 32px;
  height: 32px;
  background: ${props => props.theme.colors.gradientPrimary};
  border-radius: ${props => props.theme.borderRadius.md};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
`;

const MobileMenuButton = styled.button`
  display: none;
  background: none;
  border: none;
  color: ${props => props.theme.colors.text};
  cursor: pointer;
  padding: ${props => props.theme.spacing.sm};
  border-radius: ${props => props.theme.borderRadius.sm};

  @media (max-width: 768px) {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &:hover {
    background: ${props => props.theme.colors.backgroundTertiary};
  }
`;

const NavList = styled.ul`
  flex: 1;
  list-style: none;
  padding: ${props => props.theme.spacing.md} 0;
  overflow-y: auto;
`;

const NavItem = styled.li`
  margin: 0 ${props => props.theme.spacing.sm};
`;

const NavLinkStyled = styled(NavLink)`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
  padding: ${props => props.theme.spacing.md} ${props => props.theme.spacing.lg};
  color: ${props => props.theme.colors.textSecondary};
  text-decoration: none;
  border-radius: ${props => props.theme.borderRadius.md};
  transition: all ${props => props.theme.transitions.normal};
  font-weight: ${props => props.theme.fontWeight.medium};

  &:hover {
    background: ${props => props.theme.colors.backgroundTertiary};
    color: ${props => props.theme.colors.text};
  }

  &.active {
    background: ${props => props.theme.colors.primaryLight};
    color: ${props => props.theme.colors.primary};
    font-weight: ${props => props.theme.fontWeight.semibold};
  }

  svg {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }
`;

const UserSection = styled.div`
  padding: ${props => props.theme.spacing.lg};
  border-top: 1px solid ${props => props.theme.colors.border};
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
  padding: ${props => props.theme.spacing.md};
  background: ${props => props.theme.colors.backgroundTertiary};
  border-radius: ${props => props.theme.borderRadius.md};
  margin-bottom: ${props => props.theme.spacing.md};
`;

const UserAvatar = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: ${props => props.theme.colors.gradientPrimary};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: ${props => props.theme.fontWeight.bold};
  font-size: ${props => props.theme.fontSize.sm};
`;

const UserDetails = styled.div`
  flex: 1;
  min-width: 0;
`;

const UserName = styled.div`
  font-weight: ${props => props.theme.fontWeight.semibold};
  color: ${props => props.theme.colors.text};
  font-size: ${props => props.theme.fontSize.sm};
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const UserEmail = styled.div`
  color: ${props => props.theme.colors.textSecondary};
  font-size: ${props => props.theme.fontSize.xs};
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const UserActions = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.xs};
`;

const UserActionButton = styled.button`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  background: none;
  border: none;
  color: ${props => props.theme.colors.textSecondary};
  text-decoration: none;
  border-radius: ${props => props.theme.borderRadius.sm};
  transition: all ${props => props.theme.transitions.normal};
  font-size: ${props => props.theme.fontSize.sm};
  font-weight: ${props => props.theme.fontWeight.medium};
  cursor: pointer;
  width: 100%;
  text-align: left;

  &:hover {
    background: ${props => props.theme.colors.backgroundTertiary};
    color: ${props => props.theme.colors.text};
  }

  svg {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
  }
`;

const StatusSection = styled.div`
  padding: ${props => props.theme.spacing.lg};
  border-top: 1px solid ${props => props.theme.colors.border};
`;

const StatusTitle = styled.h3`
  font-size: ${props => props.theme.fontSize.sm};
  font-weight: ${props => props.theme.fontWeight.semibold};
  color: ${props => props.theme.colors.textSecondary};
  margin-bottom: ${props => props.theme.spacing.md};
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const StatusItem = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  padding: ${props => props.theme.spacing.sm} 0;
  font-size: ${props => props.theme.fontSize.sm};
`;

const StatusIndicator = styled.div`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${props => {
    switch (props.status) {
      case 'online': return props.theme.colors.success;
      case 'warning': return props.theme.colors.warning;
      case 'error': return props.theme.colors.error;
      default: return props.theme.colors.textTertiary;
    }
  }};
`;

const MobileOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: ${props => props.theme.zIndex.modal - 1};
  display: ${props => props.isOpen ? 'block' : 'none'};

  @media (min-width: 769px) {
    display: none;
  }
`;

const navigationItems = [
  {
    path: '/dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    description: 'Обзор системы и статистика'
  },
  {
    path: '/agents',
    label: 'Агенты',
    icon: Bot,
    description: 'Управление AI агентами'
  },
  {
    path: '/content',
    label: 'Контент',
    icon: FileText,
    description: 'Создание и управление контентом'
  },
  {
    path: '/settings',
    label: 'Настройки',
    icon: Settings,
    description: 'Конфигурация системы'
  }
];

export const Navigation = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  const closeMenu = () => {
    setIsOpen(false);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
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

  return (
    <>
      <MobileOverlay isOpen={isOpen} onClick={closeMenu} />
      <NavigationContainer isOpen={isOpen}>
        <Header>
          <Logo>
            <LogoIcon>
              <Zap size={20} />
            </LogoIcon>
            AI Orchestrator
          </Logo>
          <MobileMenuButton onClick={toggleMenu}>
            {isOpen ? <X size={20} /> : <Menu size={20} />}
          </MobileMenuButton>
        </Header>

        <NavList>
          {navigationItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavItem key={item.path}>
                <NavLinkStyled
                  to={item.path}
                  onClick={closeMenu}
                  title={item.description}
                >
                  <Icon />
                  {item.label}
                </NavLinkStyled>
              </NavItem>
            );
          })}
        </NavList>

        <UserSection>
          <UserInfo>
            <UserAvatar>{getInitials()}</UserAvatar>
            <UserDetails>
              <UserName>{user?.get_display_name || user?.username}</UserName>
              <UserEmail>{user?.email}</UserEmail>
            </UserDetails>
          </UserInfo>
          
          <UserActions>
            <UserActionButton onClick={() => navigate('/profile')}>
              <User size={16} />
              Профиль
            </UserActionButton>
            <UserActionButton onClick={handleLogout}>
              <LogOut size={16} />
              Выйти
            </UserActionButton>
          </UserActions>
        </UserSection>

        <StatusSection>
          <StatusTitle>Статус системы</StatusTitle>
          <StatusItem>
            <StatusIndicator status="online" />
            <span>API подключен</span>
          </StatusItem>
          <StatusItem>
            <StatusIndicator status="online" />
            <span>10 агентов активны</span>
          </StatusItem>
          <StatusItem>
            <StatusIndicator status="online" />
            <span>Система работает</span>
          </StatusItem>
        </StatusSection>
      </NavigationContainer>
    </>
  );
};

export default Navigation;
