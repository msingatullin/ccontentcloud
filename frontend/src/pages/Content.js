import React, { useState } from 'react';
import styled from 'styled-components';
import { 
  FileText, 
  Plus, 
  Search, 
  Filter, 
  Download,
  Eye,
  Edit,
  Trash2
} from 'lucide-react';
import { useQuery } from 'react-query';
import { contentAPI } from '../services/api';

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

const SearchBar = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.md};
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const SearchInput = styled.input`
  flex: 1;
  padding: ${props => props.theme.spacing.md};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  font-size: ${props => props.theme.fontSize.base};
  background: ${props => props.theme.colors.backgroundSecondary};

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 3px ${props => props.theme.colors.primaryLight};
  }
`;

const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: ${props => props.theme.spacing.lg};
`;

const ContentCard = styled.div`
  background: ${props => props.theme.colors.backgroundSecondary};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.lg};
  padding: ${props => props.theme.spacing.lg};
  box-shadow: ${props => props.theme.colors.shadow};
  transition: all ${props => props.theme.transitions.normal};

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
  font-size: ${props => props.theme.fontSize.lg};
  font-weight: ${props => props.theme.fontWeight.semibold};
  color: ${props => props.theme.colors.text};
  margin: 0;
`;

const CardActions = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.sm};
`;

const ActionButton = styled.button`
  width: 32px;
  height: 32px;
  border: none;
  background: ${props => props.theme.colors.backgroundTertiary};
  color: ${props => props.theme.colors.textSecondary};
  border-radius: ${props => props.theme.borderRadius.sm};
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all ${props => props.theme.transitions.normal};

  &:hover {
    background: ${props => props.theme.colors.primary};
    color: white;
  }
`;

const CardContent = styled.div`
  margin-bottom: ${props => props.theme.spacing.md};
`;

const CardDescription = styled.p`
  font-size: ${props => props.theme.fontSize.sm};
  color: ${props => props.theme.colors.textSecondary};
  margin: 0 0 ${props => props.theme.spacing.sm} 0;
  line-height: 1.5;
`;

const CardMeta = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: ${props => props.theme.fontSize.xs};
  color: ${props => props.theme.colors.textTertiary};
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
      case 'published': return props.theme.colors.successLight;
      case 'draft': return props.theme.colors.warningLight;
      case 'processing': return props.theme.colors.infoLight;
      case 'error': return props.theme.colors.errorLight;
      default: return props.theme.colors.backgroundTertiary;
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'published': return props.theme.colors.success;
      case 'draft': return props.theme.colors.warning;
      case 'processing': return props.theme.colors.info;
      case 'error': return props.theme.colors.error;
      default: return props.theme.colors.textSecondary;
    }
  }};
`;

const EmptyState = styled.div`
  text-align: center;
  padding: ${props => props.theme.spacing.xxxl};
  color: ${props => props.theme.colors.textSecondary};
`;

export const Content = () => {
  const [searchQuery, setSearchQuery] = useState('');

  // Моковые данные для демонстрации
  const mockContent = [
    {
      id: 1,
      title: 'Статья о AI в бизнесе',
      description: 'Подробное руководство по внедрению искусственного интеллекта в бизнес-процессы',
      status: 'published',
      createdAt: '2024-01-15',
      author: 'Chief Content Agent'
    },
    {
      id: 2,
      title: 'Инфографика: Тренды 2024',
      description: 'Визуальное представление основных трендов в области технологий',
      status: 'processing',
      createdAt: '2024-01-14',
      author: 'Multimedia Producer Agent'
    },
    {
      id: 3,
      title: 'Рекламный креатив для Telegram',
      description: 'A/B тест рекламных креативов для продвижения продукта',
      status: 'draft',
      createdAt: '2024-01-13',
      author: 'Paid Creative Agent'
    },
    {
      id: 4,
      title: 'Адаптация контента для соцсетей',
      description: 'Преобразование длинной статьи в серию постов для Instagram',
      status: 'published',
      createdAt: '2024-01-12',
      author: 'Repurpose Agent'
    }
  ];

  const filteredContent = mockContent.filter(item =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusText = (status) => {
    switch (status) {
      case 'published': return 'Опубликовано';
      case 'draft': return 'Черновик';
      case 'processing': return 'Обработка';
      case 'error': return 'Ошибка';
      default: return 'Неизвестно';
    }
  };

  return (
    <Container>
      <Header>
        <Title>
          <FileText size={32} />
          Управление контентом
        </Title>
        
        <Actions>
          <SecondaryButton>
            <Download size={16} />
            Экспорт
          </SecondaryButton>
          <Button>
            <Plus size={16} />
            Создать контент
          </Button>
        </Actions>
      </Header>

      <SearchBar>
        <SearchInput
          type="text"
          placeholder="Поиск контента..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <SecondaryButton>
          <Filter size={16} />
          Фильтры
        </SecondaryButton>
      </SearchBar>

      {filteredContent.length === 0 ? (
        <EmptyState>
          <FileText size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
          <p>Контент не найден</p>
        </EmptyState>
      ) : (
        <ContentGrid>
          {filteredContent.map((item) => (
            <ContentCard key={item.id}>
              <CardHeader>
                <CardTitle>{item.title}</CardTitle>
                <CardActions>
                  <ActionButton title="Просмотр">
                    <Eye size={16} />
                  </ActionButton>
                  <ActionButton title="Редактировать">
                    <Edit size={16} />
                  </ActionButton>
                  <ActionButton title="Удалить">
                    <Trash2 size={16} />
                  </ActionButton>
                </CardActions>
              </CardHeader>

              <CardContent>
                <CardDescription>{item.description}</CardDescription>
              </CardContent>

              <CardMeta>
                <div>
                  <div>Автор: {item.author}</div>
                  <div>Создано: {item.createdAt}</div>
                </div>
                <StatusBadge status={item.status}>
                  {getStatusText(item.status)}
                </StatusBadge>
              </CardMeta>
            </ContentCard>
          ))}
        </ContentGrid>
      )}
    </Container>
  );
};
