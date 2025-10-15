## 🎯 Новый функционал: Загрузка медиа и документов

### Что изменилось?

Теперь пользователи могут прикреплять файлы к запросам на создание контента:
- 📸 Изображения (jpg, png, gif, webp)
- 🎥 Видео (mp4, mov, avi)
- 📄 Документы (pdf, docx, xlsx, md, txt)

---

## 🔄 Workflow для фронтенда

### Шаг 1: Загрузить файл

**Endpoint:** `POST /uploads/upload`

**Request:**
```javascript
const formData = new FormData();
formData.append('file', fileObject);  // File из input[type="file"]
formData.append('folder', 'images');  // или 'documents', 'videos'
formData.append('analyze', 'true');   // AI анализ (опционально)

const response = await fetch('/uploads/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const result = await response.json();
```

**Response:**
```json
{
  "success": true,
  "file": {
    "id": "abc123-def456",           // ← СОХРАНИ ЭТОТ ID!
    "url": "https://storage.googleapis.com/...",
    "filename": "photo.jpg",
    "size_kb": 245,
    "type": "image",
    "ai_description": "Офис с людьми"  // если analyze=true
  },
  "ai_analysis": {
    "description": "Детальное описание",
    "mood": "professional",
    "caption": "Готовая подпись для поста"
  }
}
```

**Важно:** Сохрани `file.id` - он понадобится на шаге 2!

---

### Шаг 2: Создать контент с файлами

**Endpoint:** `POST /content/create`

**Request:**
```javascript
const contentRequest = {
  title: "AI в бизнесе",
  description: "Статья про искусственный интеллект",
  target_audience: "предприниматели",
  business_goals: ["увеличить продажи", "привлечь подписчиков"],  // МАССИВ!
  call_to_action: [  // МАССИВ! Каждый чекбокс/поле = элемент
    "Подпишитесь на наш Telegram канал",
    "https://t.me/yourchannel",
    "Переходите на сайт за подробностями",
    "https://example.com?utm_source=post"
  ],
  keywords: ["AI", "бизнес", "автоматизация"],  // МАССИВ!
  platforms: ["telegram", "vk"],
  
  // НОВОЕ - прикрепляем загруженные файлы:
  uploaded_files: ["abc123-def456", "xyz789-uvw012"],  // IDs из шага 1
  reference_urls: ["https://example.com/article"]      // опционально
};

const response = await fetch('/content/create', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(contentRequest)
});
```

---

## 📋 Дополнительные эндпоинты

### Список загруженных файлов

**Endpoint:** `GET /uploads/list?page=1&per_page=20&file_type=image`

**Response:**
```json
{
  "files": [
    {
      "id": "abc123",
      "filename": "photo.jpg",
      "url": "https://...",
      "size_kb": 245,
      "uploaded_at": "2025-10-15T10:30:00Z",
      "used_in_content": ["content_id_1"]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3
  },
  "storage": {
    "total_files": 45,
    "total_size_mb": 125.5
  }
}
```

### Детали файла

**Endpoint:** `GET /uploads/{file_id}`

**Response:**
```json
{
  "file": {
    "id": "abc123",
    "url": "https://...",
    "ai_description": "Полное описание",
    "extracted_text": "Текст из документа...",  // для PDF/DOCX
    "document_metadata": { /* метаданные */ }
  }
}
```

### Удалить файл

**Endpoint:** `DELETE /uploads/{file_id}`

**Response:**
```json
{
  "success": true,
  "message": "Файл успешно удален"
}
```

---

## ⚠️ ВАЖНЫЕ МОМЕНТЫ

### 1. Формат данных в запросах

**❌ НЕПРАВИЛЬНО:**
```javascript
{
  business_goals: "увеличить продажи. привлечь подписчиков",  // строка!
  keywords: "AI. бизнес. автоматизация"                       // строка!
}
```

**✅ ПРАВИЛЬНО:**
```javascript
{
  business_goals: ["увеличить продажи", "привлечь подписчиков"],  // массив!
  keywords: ["AI", "бизнес", "автоматизация"],                     // массив!
  call_to_action: [                                                // массив!
    "Подпишись на Telegram",
    "https://t.me/channel",
    "Получи скидку 20%"
  ]
}
```

**Почему массив?**
- Бэкенд ожидает `List[str]`
- Если отправить строку - будет ошибка валидации
- Для UI можно показывать как теги/чипсы
- Для отображения можно склеить: `businessGoals.join(', ')`

**call_to_action - особенности:**
- Каждый чекбокс + его поле = отдельный элемент
- Можно чередовать: текст, ссылка, текст, ссылка
- AI автоматически адаптирует под каждую платформу:
  - Telegram: использует все элементы
  - Instagram: только первый текст + "Ссылка в bio"
  - VK: текст + первая ссылка

---

### 2. Загрузка файлов

**Content-Type:** `multipart/form-data` (НЕ JSON!)

**Пример с React:**
```jsx
const handleFileUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('analyze', 'true');
  
  const response = await fetch('/uploads/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
      // НЕ добавляй Content-Type - браузер сам установит
    },
    body: formData
  });
  
  const result = await response.json();
  return result.file.id;  // Сохрани ID для использования
};
```

---

### 3. Лимиты

- **Размер файла:** максимум 100 MB
- **Количество файлов в запросе:** максимум 10
- **Поддерживаемые форматы:**
  - Изображения: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
  - Видео: `.mp4`, `.mov`, `.avi`
  - Документы: `.pdf`, `.docx`, `.xlsx`, `.md`, `.txt`

---

## 🎨 UI/UX рекомендации

### Компонент загрузки файлов

```jsx
<FileUploader
  accept="image/*,.pdf,.docx,.xlsx"
  maxSize={100 * 1024 * 1024}  // 100 MB
  onUpload={(fileId) => {
    // Добавь fileId в массив uploaded_files
    setUploadedFiles([...uploadedFiles, fileId]);
  }}
/>
```

### Превью загруженных файлов

```jsx
{uploadedFiles.map(fileId => (
  <FilePreview
    key={fileId}
    fileId={fileId}
    onRemove={() => {
      setUploadedFiles(uploadedFiles.filter(id => id !== fileId));
    }}
  />
))}
```

### Показать AI анализ

Если `analyze=true`, покажи пользователю что AI увидел:

```jsx
{aiAnalysis && (
  <div className="ai-insights">
    <h4>AI увидел на изображении:</h4>
    <p>{aiAnalysis.description}</p>
    <p><strong>Настроение:</strong> {aiAnalysis.mood}</p>
    <p><strong>Предложенная подпись:</strong> {aiAnalysis.caption}</p>
  </div>
)}
```

---

## 🔐 Авторизация

Все эндпоинты требуют JWT токен:

```javascript
headers: {
  'Authorization': `Bearer ${token}`
}
```

Без токена → `401 Unauthorized`

---

## 📊 Swagger UI

Все эндпоинты доступны в Swagger UI:
- `https://your-domain.com/docs`
- Секция **"File Uploads"**
- Можно протестировать прямо там

---

## 🐛 Обработка ошибок

```javascript
try {
  const response = await fetch('/uploads/upload', {...});
  const result = await response.json();
  
  if (!result.success) {
    // Показать ошибку пользователю
    showError(result.message);
  }
} catch (error) {
  // Сетевая ошибка
  showError('Ошибка загрузки файла');
}
```

**Типичные ошибки:**
- `400` - Файл не выбран или слишком большой
- `401` - Не авторизован
- `500` - Ошибка сервера (проблема с GCS)

---

## 📝 Пример полного flow

```javascript
// 1. Загрузить изображение
const uploadImage = async (imageFile) => {
  const formData = new FormData();
  formData.append('file', imageFile);
  formData.append('folder', 'images');
  formData.append('analyze', 'true');
  
  const response = await fetch('/uploads/upload', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  const { file, ai_analysis } = await response.json();
  return { fileId: file.id, aiAnalysis: ai_analysis };
};

// 2. Создать контент с изображением
const createContent = async (fileId) => {
  const response = await fetch('/content/create', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      title: "Новый пост",
      description: "Описание поста",
      target_audience: "все",
      business_goals: ["вовлечение", "продажи"],
      call_to_action: "Подпишись",
      keywords: ["тренд", "новость"],
      platforms: ["telegram"],
      uploaded_files: [fileId]  // ← Прикрепляем файл
    })
  });
  
  return await response.json();
};

// 3. Использование
const handleSubmit = async () => {
  // Загружаем файлы
  const uploadedFileIds = [];
  for (const file of selectedFiles) {
    const { fileId } = await uploadImage(file);
    uploadedFileIds.push(fileId);
  }
  
  // Создаем контент
  const result = await createContent(uploadedFileIds);
  
  if (result.success) {
    showSuccess('Контент создан!');
  }
};
```

---

## ❓ FAQ

**Q: Можно ли загрузить несколько файлов одновременно?**  
A: Нет, `/uploads/upload` принимает один файл. Загружай по одному в цикле.

**Q: Где хранятся файлы?**  
A: В Google Cloud Storage. URL публичный, можно использовать напрямую в `<img>`.

**Q: Что делать если файл слишком большой?**  
A: Показать ошибку. Лимит 100 MB. Можно сжать на фронте перед загрузкой.

**Q: Нужно ли удалять файлы если пользователь отменил создание контента?**  
A: Желательно, но не критично. Файлы с мягким удалением (`is_deleted=true`).

**Q: Как показать прогресс загрузки?**  
A: Используй `XMLHttpRequest` с `upload.onprogress` или библиотеку типа `axios`.

---

## 🚀 Готово!

Теперь у тебя есть все для интеграции загрузки файлов.

**Если что-то непонятно:**
1. Открой Swagger UI: `/docs`
2. Протестируй эндпоинты там
3. Посмотри примеры запросов/ответов

**Удачи! 🎉**

