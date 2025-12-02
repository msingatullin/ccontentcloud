import React, { useState } from 'react';
import styled from 'styled-components';
import { toast } from 'react-hot-toast';
import { Check, X, Image as ImageIcon } from 'lucide-react';

const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
`;

const ModalContent = styled.div`
  background: white;
  border-radius: 12px;
  max-width: 1200px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
`;

const ModalHeader = styled.div`
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const ModalTitle = styled.h2`
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: background 0.2s;
  
  &:hover {
    background: #f3f4f6;
  }
`;

const VariantsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  padding: 1.5rem;
`;

const VariantCard = styled.div`
  border: 2px solid ${props => props.selected ? '#3b82f6' : '#e5e7eb'};
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  background: ${props => props.selected ? '#eff6ff' : 'white'};
  
  &:hover {
    border-color: ${props => props.selected ? '#3b82f6' : '#9ca3af'};
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
`;

const VariantHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
`;

const VariantNumber = styled.div`
  font-weight: 600;
  color: #374151;
`;

const SelectedBadge = styled.div`
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: #3b82f6;
  font-size: 0.875rem;
  font-weight: 500;
`;

const VariantText = styled.div`
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 0.75rem;
  white-space: pre-wrap;
`;

const VariantImage = styled.div`
  width: 100%;
  height: 200px;
  background: #f3f4f6;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.75rem;
  color: #9ca3af;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 6px;
  }
`;

const VariantHashtags = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
`;

const Hashtag = styled.span`
  background: #f3f4f6;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #6b7280;
`;

const QualityMetrics = styled.div`
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.5rem;
`;

const Metric = styled.div`
  display: flex;
  align-items: center;
  gap: 0.25rem;
`;

const ModalFooter = styled.div`
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
`;

const Button = styled.button`
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  
  ${props => props.primary ? `
    background: #3b82f6;
    color: white;
    
    &:hover {
      background: #2563eb;
    }
    
    &:disabled {
      background: #9ca3af;
      cursor: not-allowed;
    }
  ` : `
    background: #f3f4f6;
    color: #374151;
    
    &:hover {
      background: #e5e7eb;
    }
  `}
`;

export const ContentVariantsPreview = ({ isOpen, onClose, variants, workflowId, onSelectVariant }) => {
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [isPublishing, setIsPublishing] = useState(false);

  if (!isOpen || !variants || variants.length === 0) {
    return null;
  }

  const handleSelectVariant = (variant) => {
    setSelectedVariant(variant);
  };

  const handlePublish = async () => {
    if (!selectedVariant) {
      toast.error('Выберите вариант для публикации');
      return;
    }

    setIsPublishing(true);
    try {
      if (onSelectVariant) {
        await onSelectVariant(selectedVariant, workflowId);
      }
      toast.success('Вариант выбран и будет опубликован!');
      onClose();
    } catch (error) {
      console.error('Error publishing variant:', error);
      toast.error('Ошибка публикации: ' + (error.response?.data?.message || error.message));
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <ModalOverlay onClick={onClose}>
      <ModalContent onClick={(e) => e.stopPropagation()}>
        <ModalHeader>
          <ModalTitle>Выберите вариант поста</ModalTitle>
          <CloseButton onClick={onClose}>
            <X size={24} />
          </CloseButton>
        </ModalHeader>
        
        <VariantsGrid>
          {variants.map((variant, index) => (
            <VariantCard
              key={variant.variant_number || index}
              selected={selectedVariant === variant}
              onClick={() => handleSelectVariant(variant)}
            >
              <VariantHeader>
                <VariantNumber>Вариант {variant.variant_number || index + 1}</VariantNumber>
                {selectedVariant === variant && (
                  <SelectedBadge>
                    <Check size={16} />
                    Выбран
                  </SelectedBadge>
                )}
              </VariantHeader>
              
              {variant.content?.text && (
                <VariantText>{variant.content.text}</VariantText>
              )}
              
              {variant.image_url && (
                <VariantImage>
                  <img src={variant.image_url} alt={`Вариант ${variant.variant_number || index + 1}`} />
                </VariantImage>
              )}
              
              {!variant.image_url && (
                <VariantImage>
                  <ImageIcon size={48} />
                  <span style={{ marginLeft: '0.5rem' }}>Изображение будет добавлено</span>
                </VariantImage>
              )}
              
              {variant.content?.hashtags && variant.content.hashtags.length > 0 && (
                <VariantHashtags>
                  {variant.content.hashtags.map((tag, tagIndex) => (
                    <Hashtag key={tagIndex}>#{tag}</Hashtag>
                  ))}
                </VariantHashtags>
              )}
              
              {variant.quality_metrics && (
                <QualityMetrics>
                  <Metric>
                    <span>SEO: {Math.round(variant.quality_metrics.seo_score || 0)}%</span>
                  </Metric>
                  <Metric>
                    <span>Вовлеченность: {Math.round(variant.quality_metrics.engagement_potential || 0)}%</span>
                  </Metric>
                </QualityMetrics>
              )}
            </VariantCard>
          ))}
        </VariantsGrid>
        
        <ModalFooter>
          <Button onClick={onClose}>Отмена</Button>
          <Button primary onClick={handlePublish} disabled={!selectedVariant || isPublishing}>
            {isPublishing ? 'Публикация...' : 'Опубликовать выбранный вариант'}
          </Button>
        </ModalFooter>
      </ModalContent>
    </ModalOverlay>
  );
};

