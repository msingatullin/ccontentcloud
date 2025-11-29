/**
 * ProjectSelector - Компонент выбора проекта в сайдбаре
 */

import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { ChevronDown, FolderOpen, Plus, Check, Settings } from 'lucide-react';
import { useProject } from '../../contexts/ProjectContext';

const SelectorContainer = styled.div`
  position: relative;
  margin: ${props => props.theme.spacing.md};
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const SelectorButton = styled.button`
  width: 100%;
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  padding: ${props => props.theme.spacing.md};
  background: ${props => props.theme.colors.backgroundTertiary};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  color: ${props => props.theme.colors.text};
  font-size: ${props => props.theme.fontSize.sm};
  font-weight: ${props => props.theme.fontWeight.medium};
  cursor: pointer;
  transition: all ${props => props.theme.transitions.normal};
  text-align: left;

  &:hover {
    background: ${props => props.theme.colors.backgroundSecondary};
    border-color: ${props => props.theme.colors.primary};
  }

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 2px ${props => props.theme.colors.primaryLight};
  }
`;

const IconWrapper = styled.div`
  width: 28px;
  height: 28px;
  background: ${props => props.theme.colors.gradientPrimary};
  border-radius: ${props => props.theme.borderRadius.sm};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
`;

const ProjectInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

const ProjectName = styled.div`
  font-weight: ${props => props.theme.fontWeight.semibold};
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const ProjectMeta = styled.div`
  font-size: ${props => props.theme.fontSize.xs};
  color: ${props => props.theme.colors.textSecondary};
`;

const ChevronIcon = styled(ChevronDown)`
  flex-shrink: 0;
  transition: transform 0.2s ease;
  transform: ${props => props.$isOpen ? 'rotate(180deg)' : 'rotate(0)'};
`;

const SettingsButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  color: ${props => props.theme.colors.textSecondary};
  cursor: pointer;
  border-radius: ${props => props.theme.borderRadius.sm};
  transition: all ${props => props.theme.transitions.fast};
  flex-shrink: 0;

  &:hover {
    background: ${props => props.theme.colors.backgroundTertiary};
    color: ${props => props.theme.colors.primary};
  }
`;

const Dropdown = styled.div`
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: ${props => props.theme.colors.backgroundSecondary};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  box-shadow: ${props => props.theme.colors.shadowLg};
  z-index: ${props => props.theme.zIndex.dropdown};
  max-height: 300px;
  overflow-y: auto;
  display: ${props => props.$isOpen ? 'block' : 'none'};
`;

const DropdownHeader = styled.div`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  font-size: ${props => props.theme.fontSize.xs};
  font-weight: ${props => props.theme.fontWeight.semibold};
  color: ${props => props.theme.colors.textSecondary};
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid ${props => props.theme.colors.border};
`;

const ProjectList = styled.div`
  padding: ${props => props.theme.spacing.xs} 0;
`;

const ProjectItem = styled.button`
  width: 100%;
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  background: ${props => props.$isSelected ? props.theme.colors.primaryLight : 'transparent'};
  border: none;
  color: ${props => props.$isSelected ? props.theme.colors.primary : props.theme.colors.text};
  font-size: ${props => props.theme.fontSize.sm};
  cursor: pointer;
  transition: all ${props => props.theme.transitions.fast};
  text-align: left;

  &:hover {
    background: ${props => props.$isSelected ? props.theme.colors.primaryLight : props.theme.colors.backgroundTertiary};
  }
`;

const ProjectItemIcon = styled.div`
  width: 24px;
  height: 24px;
  background: ${props => props.$isSelected ? props.theme.colors.primary : props.theme.colors.backgroundTertiary};
  border-radius: ${props => props.theme.borderRadius.sm};
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${props => props.$isSelected ? 'white' : props.theme.colors.textSecondary};
  flex-shrink: 0;
`;

const ProjectItemInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

const ProjectItemName = styled.div`
  font-weight: ${props => props.theme.fontWeight.medium};
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const CheckIcon = styled(Check)`
  flex-shrink: 0;
  color: ${props => props.theme.colors.primary};
`;

const Divider = styled.div`
  height: 1px;
  background: ${props => props.theme.colors.border};
  margin: ${props => props.theme.spacing.xs} 0;
`;

const CreateButton = styled.button`
  width: 100%;
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  background: transparent;
  border: none;
  color: ${props => props.theme.colors.primary};
  font-size: ${props => props.theme.fontSize.sm};
  font-weight: ${props => props.theme.fontWeight.medium};
  cursor: pointer;
  transition: all ${props => props.theme.transitions.fast};
  text-align: left;

  &:hover {
    background: ${props => props.theme.colors.primaryLight};
  }
`;

const LoadingState = styled.div`
  padding: ${props => props.theme.spacing.md};
  text-align: center;
  color: ${props => props.theme.colors.textSecondary};
  font-size: ${props => props.theme.fontSize.sm};
`;

const EmptyState = styled.div`
  padding: ${props => props.theme.spacing.lg};
  text-align: center;
  color: ${props => props.theme.colors.textSecondary};
  font-size: ${props => props.theme.fontSize.sm};
`;

export const ProjectSelector = () => {
  const { projects, currentProject, isLoading, selectProject, createProject } = useProject();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);
  const navigate = useNavigate();

  // Закрытие при клике вне компонента
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectProject = (projectId) => {
    selectProject(projectId);
    setIsOpen(false);
  };

  const handleCreateProject = async () => {
    const name = prompt('Введите название проекта:');
    if (name && name.trim()) {
      const result = await createProject({ name: name.trim() });
      if (result.success) {
        selectProject(result.project.id);
      }
    }
    setIsOpen(false);
  };

  const handleOpenSettings = (e) => {
    e.stopPropagation();
    if (currentProject) {
      navigate(`/dashboard/projects/${currentProject.id}/settings`);
    }
  };

  if (isLoading) {
    return (
      <SelectorContainer>
        <SelectorButton disabled>
          <IconWrapper>
            <FolderOpen size={14} />
          </IconWrapper>
          <ProjectInfo>
            <ProjectName>Загрузка...</ProjectName>
          </ProjectInfo>
        </SelectorButton>
      </SelectorContainer>
    );
  }

  return (
    <SelectorContainer ref={containerRef}>
      <SelectorButton onClick={() => setIsOpen(!isOpen)}>
        <IconWrapper>
          <FolderOpen size={14} />
        </IconWrapper>
        <ProjectInfo>
          <ProjectName>
            {currentProject?.name || 'Выберите проект'}
          </ProjectName>
          {currentProject && (
            <ProjectMeta>
              {currentProject.channels_count || 0} каналов
            </ProjectMeta>
          )}
        </ProjectInfo>
        {currentProject && (
          <SettingsButton onClick={handleOpenSettings} title="Настройки проекта">
            <Settings size={16} />
          </SettingsButton>
        )}
        <ChevronIcon size={16} $isOpen={isOpen} />
      </SelectorButton>

      <Dropdown $isOpen={isOpen}>
        <DropdownHeader>Проекты</DropdownHeader>
        
        {projects.length === 0 ? (
          <EmptyState>
            Нет проектов.<br />Создайте первый!
          </EmptyState>
        ) : (
          <ProjectList>
            {projects.map((project) => (
              <ProjectItem
                key={project.id}
                $isSelected={currentProject?.id === project.id}
                onClick={() => handleSelectProject(project.id)}
              >
                <ProjectItemIcon $isSelected={currentProject?.id === project.id}>
                  <FolderOpen size={12} />
                </ProjectItemIcon>
                <ProjectItemInfo>
                  <ProjectItemName>{project.name}</ProjectItemName>
                </ProjectItemInfo>
                {currentProject?.id === project.id && (
                  <CheckIcon size={16} />
                )}
              </ProjectItem>
            ))}
          </ProjectList>
        )}
        
        <Divider />
        
        <CreateButton onClick={handleCreateProject}>
          <Plus size={16} />
          Новый проект
        </CreateButton>
      </Dropdown>
    </SelectorContainer>
  );
};

export default ProjectSelector;


