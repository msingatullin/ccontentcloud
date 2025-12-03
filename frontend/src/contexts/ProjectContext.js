/**
 * ProjectContext - Контекст для управления проектами пользователя
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import { projectsAPI } from '../services/api';
import { useAuth } from './AuthContext';

// Создаем контекст
const ProjectContext = createContext();

// Ключ для localStorage
const CURRENT_PROJECT_KEY = 'current_project_id';

// Провайдер контекста
export function ProjectProvider({ children }) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Загрузка проектов при авторизации
  const loadProjects = useCallback(async () => {
    if (!isAuthenticated) {
      setProjects([]);
      setCurrentProject(null);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const data = await projectsAPI.getAll();
      const projectsList = Array.isArray(data) ? data : (data.projects || []);
      setProjects(projectsList);

      if (projectsList.length > 0) {
        // Пытаемся восстановить последний выбранный проект
        const savedProjectId = localStorage.getItem(CURRENT_PROJECT_KEY);
        let selectedProject = null;

        if (savedProjectId) {
          selectedProject = projectsList.find(p => p.id === parseInt(savedProjectId));
        }

        // Если не нашли сохранённый — ищем дефолтный или первый
        if (!selectedProject) {
          selectedProject = projectsList.find(p => p.is_default) || projectsList[0];
        }

        setCurrentProject(selectedProject);
        
        if (selectedProject) {
          localStorage.setItem(CURRENT_PROJECT_KEY, selectedProject.id.toString());
        }
      } else {
        setCurrentProject(null);
        localStorage.removeItem(CURRENT_PROJECT_KEY);
      }
    } catch (err) {
      console.error('Error loading projects:', err);
      setError(err.message || 'Ошибка загрузки проектов');
      setProjects([]);
      setCurrentProject(null);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  // Загружаем проекты при изменении статуса авторизации
  useEffect(() => {
    if (!authLoading) {
      loadProjects();
    }
  }, [authLoading, loadProjects]);

  // Выбор проекта
  const selectProject = useCallback((projectId) => {
    const project = projects.find(p => p.id === projectId);
    if (project) {
      setCurrentProject(project);
      localStorage.setItem(CURRENT_PROJECT_KEY, projectId.toString());
    }
  }, [projects]);

  // Создание проекта
  const createProject = useCallback(async (projectData) => {
    try {
      const response = await projectsAPI.create(projectData);
      // Извлекаем project из ответа {success: True, project: {...}}
      const newProject = response.project || response;
      
      setProjects(prev => [...prev, newProject]);
      
      // Если это первый проект — выбираем его
      if (projects.length === 0) {
        setCurrentProject(newProject);
        localStorage.setItem(CURRENT_PROJECT_KEY, newProject.id.toString());
      }
      
      toast.success('Проект создан!');
      return { success: true, project: newProject };
    } catch (err) {
      const message = err.response?.data?.error || 'Ошибка создания проекта';
      toast.error(message);
      return { success: false, error: message };
    }
  }, [projects.length]);

  // Обновление проекта
  const updateProject = useCallback(async (projectId, projectData) => {
    try {
      const response = await projectsAPI.update(projectId, projectData);
      // Извлекаем project из ответа {success: True, project: {...}}
      const updatedProject = response.project || response;
      
      setProjects(prev => prev.map(p => 
        p.id === projectId ? updatedProject : p
      ));
      
      // Обновляем текущий проект если это он
      if (currentProject?.id === projectId) {
        setCurrentProject(updatedProject);
      }
      
      toast.success('Проект обновлён!');
      return { success: true, project: updatedProject };
    } catch (err) {
      const message = err.response?.data?.error || 'Ошибка обновления проекта';
      toast.error(message);
      return { success: false, error: message };
    }
  }, [currentProject]);

  // Удаление проекта
  const deleteProject = useCallback(async (projectId) => {
    try {
      await projectsAPI.delete(projectId);
      
      setProjects(prev => prev.filter(p => p.id !== projectId));
      
      // Если удалили текущий проект — выбираем другой
      if (currentProject?.id === projectId) {
        const remaining = projects.filter(p => p.id !== projectId);
        const newCurrent = remaining.find(p => p.is_default) || remaining[0] || null;
        setCurrentProject(newCurrent);
        
        if (newCurrent) {
          localStorage.setItem(CURRENT_PROJECT_KEY, newCurrent.id.toString());
        } else {
          localStorage.removeItem(CURRENT_PROJECT_KEY);
        }
      }
      
      toast.success('Проект удалён');
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.error || 'Ошибка удаления проекта';
      toast.error(message);
      return { success: false, error: message };
    }
  }, [currentProject, projects]);

  // Перезагрузка проектов
  const refreshProjects = useCallback(() => {
    return loadProjects();
  }, [loadProjects]);

  // Значение контекста
  const value = {
    // Состояние
    projects,
    currentProject,
    isLoading,
    error,
    hasProjects: projects.length > 0,
    
    // Методы
    selectProject,
    createProject,
    updateProject,
    deleteProject,
    refreshProjects,
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
}

// Хук для использования контекста
export function useProject() {
  const context = useContext(ProjectContext);
  
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  
  return context;
}

export default ProjectContext;



