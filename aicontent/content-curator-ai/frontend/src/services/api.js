import axios from 'axios';
import toast from 'react-hot-toast';

// Базовый URL API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://content-curator-1046574462613.us-central1.run.app';

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 секунд
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор для запросов
api.interceptors.request.use(
  (config) => {
    // Добавляем timestamp для предотвращения кэширования
    config.params = {
      ...config.params,
      _t: Date.now(),
    };
    
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Интерцептор для ответов
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error);
    
    // Обработка различных типов ошибок
    if (error.response) {
      // Сервер ответил с кодом ошибки
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          toast.error('Некорректные данные запроса');
          break;
        case 401:
          toast.error('Необходима авторизация');
          break;
        case 403:
          toast.error('Доступ запрещен');
          break;
        case 404:
          toast.error('Ресурс не найден');
          break;
        case 429:
          toast.error('Слишком много запросов. Попробуйте позже');
          break;
        case 500:
          toast.error('Внутренняя ошибка сервера');
          break;
        default:
          toast.error(data?.message || 'Произошла ошибка');
      }
    } else if (error.request) {
      // Запрос был отправлен, но ответа не получено
      toast.error('Сервер недоступен. Проверьте подключение к интернету');
    } else {
      // Что-то пошло не так при настройке запроса
      toast.error('Ошибка настройки запроса');
    }
    
    return Promise.reject(error);
  }
);

// API методы для работы с агентами
export const agentsAPI = {
  // Получить статус всех агентов
  getAgentsStatus: async () => {
    const response = await api.get('/api/v1/agents/status');
    return response.data;
  },

  // Получить информацию о конкретном агенте
  getAgentInfo: async (agentId) => {
    const response = await api.get(`/api/v1/agents/${agentId}`);
    return response.data;
  },

  // Выполнить задачу агентом
  executeTask: async (agentId, taskData) => {
    const response = await api.post(`/api/v1/agents/${agentId}/execute`, taskData);
    return response.data;
  },
};

// API методы для работы с контентом
export const contentAPI = {
  // Создать контент
  createContent: async (contentData) => {
    const response = await api.post('/api/v1/content/create', contentData);
    return response.data;
  },

  // Получить статус workflow
  getWorkflowStatus: async (workflowId) => {
    const response = await api.get(`/api/v1/workflow/${workflowId}/status`);
    return response.data;
  },

  // Получить историю контента
  getContentHistory: async (params = {}) => {
    const response = await api.get('/api/v1/content/history', { params });
    return response.data;
  },
};

// API методы для работы с системой
export const systemAPI = {
  // Получить статус системы
  getSystemStatus: async () => {
    const response = await api.get('/api/v1/system/status');
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

// API методы для работы с чатом
export const chatAPI = {
  // Отправить сообщение в чат
  sendMessage: async (message) => {
    const response = await api.post('/api/v1/chat/message', { message });
    return response.data;
  },

  // Получить историю чата
  getChatHistory: async (params = {}) => {
    const response = await api.get('/api/v1/chat/history', { params });
    return response.data;
  },
};

// API методы для работы с уведомлениями
export const notificationsAPI = {
  // Получить уведомления
  getNotifications: async () => {
    const response = await api.get('/api/v1/notifications');
    return response.data;
  },

  // Отметить уведомление как прочитанное
  markAsRead: async (notificationId) => {
    const response = await api.patch(`/api/v1/notifications/${notificationId}/read`);
    return response.data;
  },
};

// Утилитарные функции
export const apiUtils = {
  // Проверить подключение к API
  checkConnection: async () => {
    try {
      const response = await api.get('/health');
      return response.status === 200;
    } catch (error) {
      return false;
    }
  },

  // Получить базовую информацию о системе
  getSystemInfo: async () => {
    try {
      const [health, systemStatus] = await Promise.all([
        api.get('/health'),
        api.get('/api/v1/system/status')
      ]);
      
      return {
        health: health.data,
        system: systemStatus.data,
        connected: true
      };
    } catch (error) {
      return {
        connected: false,
        error: error.message
      };
    }
  },
};

// Экспортируем основной экземпляр API
export default api;
