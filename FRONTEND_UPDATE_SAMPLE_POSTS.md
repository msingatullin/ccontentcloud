# 🎨 ОБНОВЛЕНИЕ ФРОНТЕНДА: Примеры постов с изображениями

## 📋 ЧТО ИЗМЕНИЛОСЬ В API

### Endpoint: `POST /api/v1/ai/generate-sample-posts`

**Новая структура ответа:**

```typescript
{
  success: true,
  data: {
    posts: [
      {
        id: "1",
        text: "Текст поста...",
        style: "informative|selling|engaging",
        hashtags: ["#хештег1", "#хештег2"],
        image_prompt: "Краткое описание изображения для этого поста",
        image_url: "/path/to/generated/image.jpg" | null,  // НОВОЕ ПОЛЕ
        image_id: "cache_key_123" | null  // НОВОЕ ПОЛЕ
      }
    ]
  }
}
```

## ✅ ЧТО НУЖНО СДЕЛАТЬ НА ФРОНТЕНДЕ

### 1. Обновить TypeScript интерфейсы

```typescript
interface SamplePost {
  id: string;
  text: string;
  style: 'informative' | 'selling' | 'engaging';
  hashtags: string[];
  image_prompt?: string;  // НОВОЕ
  image_url?: string | null;  // НОВОЕ
  image_id?: string | null;  // НОВОЕ
}

interface GenerateSamplePostsResponse {
  success: boolean;
  data: {
    posts: SamplePost[];
  };
}
```

### 2. Отобразить изображения в UI

**Важно:** Изображения генерируются асинхронно, поэтому `image_url` может быть `null` во время генерации.

**Пример компонента:**

```tsx
interface PostPreviewProps {
  post: SamplePost;
}

const PostPreview: React.FC<PostPreviewProps> = ({ post }) => {
  const [imageLoading, setImageLoading] = useState(false);
  const [imageError, setImageError] = useState(false);
  
  // Если image_url - это путь к файлу на сервере, нужно конвертировать в URL
  const imageUrl = post.image_url 
    ? post.image_url.startsWith('http') 
      ? post.image_url 
      : `${API_BASE_URL}${post.image_url}`  // или через CDN
    : null;
  
  return (
    <div className="post-preview">
      {/* Изображение */}
      {imageUrl ? (
        <div className="post-image">
          <img 
            src={imageUrl} 
            alt={post.image_prompt || 'Post image'}
            onLoad={() => setImageLoading(false)}
            onError={() => {
              setImageError(true);
              setImageLoading(false);
            }}
          />
          {imageLoading && <div className="image-loading">Загрузка...</div>}
          {imageError && (
            <div className="image-error">
              Изображение не загрузилось
            </div>
          )}
        </div>
      ) : (
        <div className="post-image-placeholder">
          <div className="placeholder-content">
            <span>🖼️</span>
            <p>Генерация изображения...</p>
            {post.image_prompt && (
              <small>{post.image_prompt}</small>
            )}
          </div>
        </div>
      )}
      
      {/* Текст поста */}
      <div className="post-text">
        {post.text}
      </div>
      
      {/* Хештеги */}
      {post.hashtags && post.hashtags.length > 0 && (
        <div className="post-hashtags">
          {post.hashtags.map((tag, idx) => (
            <span key={idx} className="hashtag">{tag}</span>
          ))}
        </div>
      )}
      
      {/* Стиль поста */}
      <div className="post-style">
        <span className={`style-badge style-${post.style}`}>
          {post.style === 'informative' && '📊 Информационный'}
          {post.style === 'selling' && '💰 Продающий'}
          {post.style === 'engaging' && '💬 Вовлекающий'}
        </span>
      </div>
    </div>
  );
};
```

### 3. Обработка ошибок генерации изображений

Если `image_url === null`, это может означать:
- Изображение еще генерируется (в будущем можно добавить polling)
- Произошла ошибка генерации (показываем placeholder)

**Рекомендация:** Показывать placeholder с текстом `post.image_prompt`, если изображение не загрузилось.

### 4. Стилизация (CSS пример)

```css
.post-preview {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.post-image {
  width: 100%;
  aspect-ratio: 1 / 1; /* Квадратное изображение */
  background: #f5f5f5;
  position: relative;
}

.post-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.post-image-placeholder {
  width: 100%;
  aspect-ratio: 1 / 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.placeholder-content {
  text-align: center;
}

.placeholder-content span {
  font-size: 48px;
  display: block;
  margin-bottom: 10px;
}

.placeholder-content p {
  margin: 0;
  font-weight: 500;
}

.placeholder-content small {
  display: block;
  margin-top: 8px;
  opacity: 0.8;
  font-size: 12px;
}

.post-text {
  padding: 16px;
  font-size: 14px;
  line-height: 1.6;
}

.post-hashtags {
  padding: 0 16px 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hashtag {
  color: #667eea;
  font-size: 12px;
}

.post-style {
  padding: 8px 16px;
  border-top: 1px solid #e0e0e0;
}

.style-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.style-informative {
  background: #e3f2fd;
  color: #1976d2;
}

.style-selling {
  background: #fff3e0;
  color: #f57c00;
}

.style-engaging {
  background: #f3e5f5;
  color: #7b1fa2;
}
```

## 🔍 ПРОВЕРКА

1. ✅ Проверить, что `image_url` и `image_id` правильно обрабатываются
2. ✅ Показывать placeholder, если изображение не загрузилось
3. ✅ Отображать `image_prompt` в placeholder для лучшего UX
4. ✅ Обрабатывать случаи, когда `image_url === null`

## 📝 ЗАМЕТКИ

- Изображения генерируются на бэкенде через Vertex AI Imagen / DALL-E
- Путь к изображению может быть локальным (`/path/to/image.jpg`) - нужно конвертировать в URL
- В будущем можно добавить polling для проверки статуса генерации изображений
- Если изображение не сгенерировалось, показываем placeholder с `image_prompt`

