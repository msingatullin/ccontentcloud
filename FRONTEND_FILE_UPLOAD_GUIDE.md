# 📤 Гайд по загрузке файлов для фронтенд-разработчика

## ✅ ПРОСТОЙ СПОСОБ: Batch Upload (Рекомендуется)

### Один запрос для всех файлов

```javascript
// 1. Пользователь выбрал 13 файлов
const files = document.getElementById('fileInput').files; // 13 files

// 2. Создаем FormData
const formData = new FormData();

// 3. Добавляем все файлы с одним ключом 'files'
for (let i = 0; i < files.length; i++) {
  formData.append('files', files[i]);
}

// Опционально
formData.append('folder', 'images');
formData.append('analyze', 'true'); // AI анализ

// 4. Отправляем ОДИН запрос
const response = await fetch('/uploads/batch', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const result = await response.json();

// 5. Получаем массив file_id
console.log(result.uploaded_files);
/*
[
  { file_id: "uuid-1", filename: "photo1.jpg", file_type: "image" },
  { file_id: "uuid-2", filename: "photo2.jpg", file_type: "image" },
  { file_id: "uuid-3", filename: "doc.pdf", file_type: "document" },
  ...
]
*/

// 6. Извлекаем только ID для передачи в /content/create
const fileIds = result.uploaded_files.map(f => f.file_id);
// ["uuid-1", "uuid-2", "uuid-3", ...]

// 7. Используем в создании контента
const contentRequest = {
  title: "Мой пост",
  uploaded_files: fileIds,  // Вот эти ID
  // ... остальные поля
};

await fetch('/content/create', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(contentRequest)
});
```

---

## API Endpoint

### POST `/uploads/batch`

**Параметры:**
- `files` - массив файлов (до 20 штук)
- `folder` - опционально ("images", "documents", "videos")
- `analyze` - опционально (true/false) - AI анализ

**Ответ:**
```json
{
  "success": true,
  "message": "Загружено 13 из 13 файлов",
  "uploaded_files": [
    {
      "file_id": "uuid-1",
      "filename": "photo1.jpg",
      "file_type": "image",
      "file_size": 245678,
      "storage_url": "https://..."
    },
    ...
  ],
  "errors": null
}
```

**В случае ошибок:**
```json
{
  "success": true,
  "message": "Загружено 12 из 13 файлов",
  "uploaded_files": [...], // 12 успешных
  "errors": [
    {
      "filename": "broken.jpg",
      "error": "Invalid file format"
    }
  ]
}
```

---

## React пример

```jsx
function FileUploader() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadedIds, setUploadedIds] = useState([]);

  const handleUpload = async () => {
    setUploading(true);
    
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    try {
      const response = await fetch('/uploads/batch', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const result = await response.json();
      
      // Сохраняем ID для использования
      const ids = result.uploaded_files.map(f => f.file_id);
      setUploadedIds(ids);
      
      console.log(`Загружено ${ids.length} файлов`);
      
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input 
        type="file" 
        multiple 
        onChange={(e) => setFiles(Array.from(e.target.files))}
      />
      <button onClick={handleUpload} disabled={uploading}>
        {uploading ? 'Загрузка...' : `Загрузить ${files.length} файлов`}
      </button>
      
      {uploadedIds.length > 0 && (
        <p>✅ Загружено {uploadedIds.length} файлов</p>
      )}
    </div>
  );
}
```

---

## Прогресс загрузки (опционально)

Если нужен прогресс-бар:

```javascript
const xhr = new XMLHttpRequest();

// Отслеживаем прогресс
xhr.upload.addEventListener('progress', (e) => {
  if (e.lengthComputable) {
    const percentComplete = (e.loaded / e.total) * 100;
    console.log(`Загружено: ${percentComplete}%`);
    setProgress(percentComplete);
  }
});

xhr.addEventListener('load', () => {
  const result = JSON.parse(xhr.responseText);
  const ids = result.uploaded_files.map(f => f.file_id);
  setUploadedIds(ids);
});

xhr.open('POST', '/uploads/batch');
xhr.setRequestHeader('Authorization', `Bearer ${token}`);
xhr.send(formData);
```

---

## Лимиты

- **Максимум файлов за раз:** 20
- **Максимальный размер файла:** зависит от настроек сервера (обычно 10MB)
- **Поддерживаемые форматы:**
  - Изображения: jpg, jpeg, png, gif, webp
  - Видео: mp4, mov, avi
  - Документы: pdf, docx, xlsx, md, txt

---

## Старый способ (НЕ РЕКОМЕНДУЕТСЯ)

Если по каким-то причинам нужно загружать по одному:

### POST `/uploads/upload` - один файл

```javascript
// Загружать каждый файл отдельно (медленно!)
const fileIds = [];

for (const file of files) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/uploads/upload', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  const result = await response.json();
  fileIds.push(result.file_id);
}

// Теперь используем fileIds
```

**Минусы:**
- 13 файлов = 13 HTTP запросов (медленно)
- Больше нагрузки на сервер
- Хуже UX (долго ждать)

---

## Полный workflow

```
┌─────────────────────────┐
│ 1. Пользователь         │
│    выбирает 13 файлов   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 2. POST /uploads/batch  │
│    с 13 файлами         │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 3. Бэкенд загружает     │
│    в Google Cloud       │
│    Storage              │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 4. Возвращает массив    │
│    из 13 file_id        │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 5. POST /content/create │
│    {                    │
│      uploaded_files: [  │
│        "uuid-1",        │
│        "uuid-2",        │
│        ...              │
│      ]                  │
│    }                    │
└─────────────────────────┘
```

---

## Обработка ошибок

```javascript
try {
  const response = await fetch('/uploads/batch', {...});
  const result = await response.json();
  
  if (!response.ok) {
    throw new Error(result.message || 'Upload failed');
  }
  
  // Проверяем были ли ошибки
  if (result.errors && result.errors.length > 0) {
    console.warn('Некоторые файлы не загрузились:', result.errors);
    // Показываем пользователю какие файлы failed
  }
  
  // Используем успешно загруженные
  const ids = result.uploaded_files.map(f => f.file_id);
  
} catch (error) {
  console.error('Upload error:', error);
  alert('Ошибка загрузки файлов');
}
```

---

## FAQ

### Q: Можно загрузить больше 20 файлов?
A: Да, разбейте на несколько запросов по 20 файлов.

```javascript
const chunkSize = 20;
const allFileIds = [];

for (let i = 0; i < files.length; i += chunkSize) {
  const chunk = files.slice(i, i + chunkSize);
  const formData = new FormData();
  chunk.forEach(f => formData.append('files', f));
  
  const response = await fetch('/uploads/batch', {...});
  const result = await response.json();
  
  allFileIds.push(...result.uploaded_files.map(f => f.file_id));
}
```

### Q: Что если загрузка прервалась?
A: Уже загруженные файлы сохранены. Повторите загрузку только failed файлов.

### Q: Можно удалить загруженный файл?
A: Да, используйте `DELETE /uploads/{file_id}`

### Q: Сколько хранятся файлы?
A: 90 дней с момента последнего использования (auto-cleanup)

---

## Готово! 🎉

**Рекомендация:** Всегда используйте `/uploads/batch` для загрузки файлов.

Один запрос = быстрее + удобнее + меньше нагрузки.

