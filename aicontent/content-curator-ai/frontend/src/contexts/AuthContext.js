/**
 * AuthContext - Контекст для управления состоянием аутентификации
 */

import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-hot-toast';
import api from '../services/api';

// Создаем контекст
const AuthContext = createContext();

// Начальное состояние
const initialState = {
  user: null,
  tokens: {
    access_token: null,
    refresh_token: null
  },
  isAuthenticated: false,
  isLoading: true,
  error: null
};

// Типы действий
const AUTH_ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_USER: 'SET_USER',
  SET_TOKENS: 'SET_TOKENS',
  SET_ERROR: 'SET_ERROR',
  LOGOUT: 'LOGOUT',
  CLEAR_ERROR: 'CLEAR_ERROR'
};

// Редьюсер для управления состоянием
function authReducer(state, action) {
  switch (action.type) {
    case AUTH_ACTIONS.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload
      };
    
    case AUTH_ACTIONS.SET_USER:
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        isLoading: false,
        error: null
      };
    
    case AUTH_ACTIONS.SET_TOKENS:
      return {
        ...state,
        tokens: action.payload,
        isLoading: false,
        error: null
      };
    
    case AUTH_ACTIONS.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        isLoading: false
      };
    
    case AUTH_ACTIONS.LOGOUT:
      return {
        ...initialState,
        isLoading: false
      };
    
    case AUTH_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null
      };
    
    default:
      return state;
  }
}

// Провайдер контекста
export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const queryClient = useQueryClient();

  // Проверка токена при загрузке
  useEffect(() => {
    const checkAuth = async () => {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (accessToken && refreshToken) {
        try {
          // Устанавливаем токен в API клиент
          api.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
          
          // Проверяем валидность токена
          const response = await api.get('/auth/me');
          
          dispatch({
            type: AUTH_ACTIONS.SET_USER,
            payload: response.data.user
          });
          
          dispatch({
            type: AUTH_ACTIONS.SET_TOKENS,
            payload: {
              access_token: accessToken,
              refresh_token: refreshToken
            }
          });
        } catch (error) {
          // Если токен невалиден, пытаемся обновить
          if (error.response?.status === 401) {
            try {
              await refreshTokens();
            } catch (refreshError) {
              // Если не удалось обновить, выходим
              logout();
            }
          } else {
            logout();
          }
        }
      } else {
        dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
      }
    };

    checkAuth();
  }, []);

  // Функция обновления токенов
  const refreshTokens = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post('/auth/refresh', {
      refresh_token: refreshToken
    });

    const { access_token, refresh_token: newRefreshToken } = response.data;
    
    // Сохраняем новые токены
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', newRefreshToken);
    
    // Обновляем заголовок авторизации
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    
    dispatch({
      type: AUTH_ACTIONS.SET_TOKENS,
      payload: {
        access_token,
        refresh_token: newRefreshToken
      }
    });

    return { access_token, refresh_token: newRefreshToken };
  };

  // Функция входа
  const login = async (email, password) => {
    try {
      dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: true });
      dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });

      const response = await api.post('/auth/login', {
        email,
        password
      });

      const { access_token, refresh_token, user } = response.data;
      
      // Сохраняем токены
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // Устанавливаем заголовок авторизации
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      dispatch({
        type: AUTH_ACTIONS.SET_USER,
        payload: user
      });
      
      dispatch({
        type: AUTH_ACTIONS.SET_TOKENS,
        payload: {
          access_token,
          refresh_token
        }
      });

      toast.success('Успешный вход в систему!');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.error || 'Ошибка при входе в систему';
      dispatch({
        type: AUTH_ACTIONS.SET_ERROR,
        payload: message
      });
      toast.error(message);
      return { success: false, error: message };
    }
  };

  // Функция регистрации
  const register = async (userData) => {
    try {
      dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: true });
      dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });

      const response = await api.post('/auth/register', userData);
      
      dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
      
      toast.success('Регистрация успешна! Проверьте email для подтверждения.');
      return { success: true, user: response.data.user };
    } catch (error) {
      const message = error.response?.data?.error || 'Ошибка при регистрации';
      dispatch({
        type: AUTH_ACTIONS.SET_ERROR,
        payload: message
      });
      toast.error(message);
      return { success: false, error: message };
    }
  };

  // Функция выхода
  const logout = async () => {
    try {
      // Отзываем токен на сервере
      await api.post('/auth/logout');
    } catch (error) {
      // Игнорируем ошибки при выходе
      console.warn('Error during logout:', error);
    } finally {
      // Очищаем локальное хранилище
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      // Удаляем заголовок авторизации
      delete api.defaults.headers.common['Authorization'];
      
      // Очищаем кеш React Query
      queryClient.clear();
      
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
      toast.success('Вы вышли из системы');
    }
  };

  // Функция обновления профиля
  const updateProfile = async (profileData) => {
    try {
      const response = await api.put('/auth/profile', profileData);
      
      dispatch({
        type: AUTH_ACTIONS.SET_USER,
        payload: response.data.user
      });
      
      toast.success('Профиль обновлен!');
      return { success: true, user: response.data.user };
    } catch (error) {
      const message = error.response?.data?.error || 'Ошибка при обновлении профиля';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  // Функция смены пароля
  const changePassword = async (currentPassword, newPassword) => {
    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      });
      
      toast.success('Пароль успешно изменен!');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.error || 'Ошибка при смене пароля';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  // Функция верификации email
  const verifyEmail = async (token) => {
    try {
      await api.post('/auth/verify-email', { token });
      toast.success('Email успешно подтвержден!');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.error || 'Ошибка при подтверждении email';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  // Функция запроса сброса пароля
  const forgotPassword = async (email) => {
    try {
      await api.post('/auth/forgot-password', { email });
      toast.success('Инструкции по сбросу пароля отправлены на email');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.error || 'Ошибка при запросе сброса пароля';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  // Функция сброса пароля
  const resetPassword = async (token, newPassword) => {
    try {
      await api.post('/auth/reset-password', {
        token,
        new_password: newPassword
      });
      toast.success('Пароль успешно сброшен!');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.error || 'Ошибка при сбросе пароля';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  // Значение контекста
  const value = {
    // Состояние
    user: state.user,
    tokens: state.tokens,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,
    
    // Функции
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    verifyEmail,
    forgotPassword,
    resetPassword,
    refreshTokens,
    
    // Утилиты
    clearError: () => dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR })
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Хук для использования контекста
export function useAuth() {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}

// Хук для проверки аутентификации
export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuth();
  
  return {
    isAuthenticated,
    isLoading,
    shouldRedirect: !isLoading && !isAuthenticated
  };
}

export default AuthContext;
