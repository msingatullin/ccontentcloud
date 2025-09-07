/**
 * ProtectedRoute - Компонент для защиты маршрутов
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import styled from 'styled-components';
import { Loader2 } from 'lucide-react';

const LoadingContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
`;

const LoadingCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  text-align: center;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
`;

const LoadingSpinner = styled.div`
  width: 40px;
  height: 40px;
  border: 3px solid rgba(6, 182, 212, 0.3);
  border-top: 3px solid #06b6d4;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const LoadingText = styled.p`
  color: #e2e8f0;
  font-size: 16px;
  margin: 0;
`;

function ProtectedRoute({ children, requireVerified = false, requireRole = null }) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  // Показываем загрузку пока проверяем аутентификацию
  if (isLoading) {
    return (
      <LoadingContainer>
        <LoadingCard>
          <LoadingSpinner />
          <LoadingText>Проверка авторизации...</LoadingText>
        </LoadingCard>
      </LoadingContainer>
    );
  }

  // Если пользователь не аутентифицирован, перенаправляем на страницу входа
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Если требуется подтвержденный email
  if (requireVerified && !user?.is_verified) {
    return <Navigate to="/verify-email" replace />;
  }

  // Если требуется определенная роль
  if (requireRole && user?.role !== requireRole) {
    return <Navigate to="/unauthorized" replace />;
  }

  // Если все проверки пройдены, показываем защищенный контент
  return children;
}

// Компонент для проверки ролей
export function RequireRole({ children, roles = [] }) {
  const { user } = useAuth();
  
  if (!user || !roles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }
  
  return children;
}

// Компонент для проверки верификации email
export function RequireVerified({ children }) {
  const { user } = useAuth();
  
  if (!user?.is_verified) {
    return <Navigate to="/verify-email" replace />;
  }
  
  return children;
}

// Компонент для отображения только неаутентифицированным пользователям
export function PublicRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <LoadingContainer>
        <LoadingCard>
          <LoadingSpinner />
          <LoadingText>Загрузка...</LoadingText>
        </LoadingCard>
      </LoadingContainer>
    );
  }

  if (isAuthenticated) {
    // Перенаправляем аутентифицированных пользователей на главную страницу
    const from = location.state?.from?.pathname || '/dashboard';
    return <Navigate to={from} replace />;
  }

  return children;
}

export default ProtectedRoute;
