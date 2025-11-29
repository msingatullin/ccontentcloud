# 📤 Пошаговая инструкция: От выбора файла до отправки

## Шаг 1: HTML - Пользователь выбирает файлы

```html
<!-- Простой input для выбора файлов -->
<input 
  type="file" 
  id="fileInput" 
  multiple 
  accept="image/*,video/*,.pdf,.docx"
/>

<button id="uploadBtn">Загрузить файлы</button>
```

**Что происходит:**
- Пользователь кликает на input
- Выбирает 3 файла: `photo1.jpg`, `photo2.jpg`, `doc.pdf`
- Браузер сохраняет их в `fileInput.files`

---

## Шаг 2: JavaScript - Получаем выбранные файлы

```javascript
// Получаем элемент input
const fileInput = document.getElementById('fileInput');

// Получаем выбранные файлы
const files = fileInput.files; // FileList объект

console.log(files); 
// FileList(3) [File, File, File]
//   0: File {name: "photo1.jpg", size: 245678, type: "image/jpeg"}
//   1: File {name: "photo2.jpg", size: 189234, type: "image/jpeg"}
//   2: File {name: "doc.pdf", size: 445123, type: "application/pdf"}
```

**Важно:** `files` - это не обычный массив, это `FileList` объект!

---

## Шаг 3: Создаем FormData и добавляем файлы

```javascript
// Создаем FormData (это специальный объект для отправки файлов)
const formData = new FormData();

// Добавляем каждый файл с ключом 'files'
for (let i = 0; i < files.length; i++) {
  const file = files[i]; // Получаем один файл
  formData.append('files', file); // Добавляем в FormData
}

// Или через современный синтаксис:
Array.from(files).forEach(file => {
  formData.append('files', file);
});

console.log('FormData готов');
// FormData теперь содержит:
//   files: photo1.jpg
//   files: photo2.jpg
//   files: doc.pdf
```

**Ключевой момент:** Все файлы добавляются с **одним ключом** `'files'`

---

## Шаг 4: Отправляем на сервер

```javascript
// Отправляем POST запрос
const response = await fetch('https://your-api.com/uploads/batch', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your-jwt-token'
    // НЕ добавляем 'Content-Type'! FormData сделает это сам
  },
  body: formData // ← Вот здесь передаем FormData
});

// Получаем ответ
const result = await response.json();

console.log(result);
// {
//   success: true,
//   uploaded_files: [
//     {file_id: "uuid-1", filename: "photo1.jpg"},
//     {file_id: "uuid-2", filename: "photo2.jpg"},
//     {file_id: "uuid-3", filename: "doc.pdf"}
//   ]
// }
```

---

## Шаг 5: Извлекаем file_id для использования

```javascript
// Извлекаем только ID
const fileIds = result.uploaded_files.map(file => file.file_id);

console.log(fileIds);
// ["uuid-1", "uuid-2", "uuid-3"]
```

---

## Шаг 6: Используем в создании контента

```javascript
// Теперь передаем эти ID в /content/create
const contentRequest = {
  title: "Мой новый пост",
  description: "Описание",
  platforms: ["telegram", "vk"],
  uploaded_files: fileIds, // ← Вот здесь используем ID
  // ... остальные поля
};

const contentResponse = await fetch('https://your-api.com/content/create', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your-jwt-token',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(contentRequest)
});
```

---

## 🎯 Полный пример (React)

```jsx
import React, { useState } from 'react';

function ContentCreator() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadedFileIds, setUploadedFileIds] = useState([]);
  const [uploading, setUploading] = useState(false);
  
  const token = 'your-jwt-token'; // Получаем из контекста/стора

  // Шаг 1-2: Обработка выбора файлов
  const handleFileSelect = (event) => {
    const files = event.target.files;
    setSelectedFiles(Array.from(files));
    console.log(`Выбрано файлов: ${files.length}`);
  };

  // Шаг 3-5: Загрузка файлов
  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      alert('Выберите файлы');
      return;
    }

    setUploading(true);

    try {
      // Шаг 3: Создаем FormData
      const formData = new FormData();
      
      selectedFiles.forEach(file => {
        formData.append('files', file); // Все с ключом 'files'
      });

      // Шаг 4: Отправляем на сервер
      const response = await fetch('/uploads/batch', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const result = await response.json();

      if (result.success) {
        // Шаг 5: Извлекаем ID
        const ids = result.uploaded_files.map(f => f.file_id);
        setUploadedFileIds(ids);
        
        alert(`Успешно загружено ${ids.length} файлов!`);
      } else {
        alert('Ошибка загрузки');
      }

    } catch (error) {
      console.error('Upload error:', error);
      alert('Ошибка загрузки файлов');
    } finally {
      setUploading(false);
    }
  };

  // Шаг 6: Создание контента с загруженными файлами
  const handleCreateContent = async () => {
    if (uploadedFileIds.length === 0) {
      alert('Сначала загрузите файлы');
      return;
    }

    const contentRequest = {
      title: "Мой пост",
      description: "Описание поста",
      platforms: ["telegram"],
      uploaded_files: uploadedFileIds, // ← Используем загруженные ID
      business_goals: ["Увеличить продажи"],
      keywords: ["AI", "бизнес"],
      call_to_action: ["Подписаться", "Купить"],
      target_audience: "Предприниматели"
    };

    try {
      const response = await fetch('/content/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(contentRequest)
      });

      const result = await response.json();
      
      if (result.success) {
        alert('Контент создан!');
      }
    } catch (error) {
      console.error('Content creation error:', error);
    }
  };

  return (
    <div>
      <h2>Создание контента</h2>
      
      {/* Шаг 1: Выбор файлов */}
      <div>
        <input 
          type="file" 
          multiple 
          onChange={handleFileSelect}
          accept="image/*,video/*,.pdf,.docx"
        />
        <p>Выбрано файлов: {selectedFiles.length}</p>
      </div>

      {/* Шаг 2-5: Загрузка */}
      <button 
        onClick={handleUpload} 
        disabled={uploading || selectedFiles.length === 0}
      >
        {uploading ? 'Загрузка...' : `Загрузить ${selectedFiles.length} файлов`}
      </button>

      {/* Показываем загруженные */}
      {uploadedFileIds.length > 0 && (
        <div>
          <p>✅ Загружено {uploadedFileIds.length} файлов</p>
          <ul>
            {uploadedFileIds.map((id, index) => (
              <li key={id}>
                Файл {index + 1}: {id}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Шаг 6: Создание контента */}
      <button 
        onClick={handleCreateContent}
        disabled={uploadedFileIds.length === 0}
      >
        Создать контент с файлами
      </button>
    </div>
  );
}

export default ContentCreator;
```

---

## 🔍 Визуализация потока данных

```
┌─────────────────────────────────────┐
│ 1. User Interface                   │
│                                     │
│  <input type="file" multiple />     │
│  [Выбрать файлы]                    │
└──────────────┬──────────────────────┘
               │ Пользователь выбирает:
               │ photo1.jpg, photo2.jpg, doc.pdf
               ▼
┌─────────────────────────────────────┐
│ 2. JavaScript получает файлы        │
│                                     │
│  const files = input.files;         │
│  FileList(3) [File, File, File]     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 3. Создаем FormData                 │
│                                     │
│  const formData = new FormData();   │
│  formData.append('files', file1);   │
│  formData.append('files', file2);   │
│  formData.append('files', file3);   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 4. POST /uploads/batch              │
│                                     │
│  fetch('/uploads/batch', {          │
│    method: 'POST',                  │
│    body: formData                   │
│  })                                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 5. Бэкенд обрабатывает              │
│                                     │
│  files = request.files.getlist()    │
│  Загружает в Google Cloud Storage   │
│  Возвращает file_id для каждого     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 6. Ответ сервера                    │
│                                     │
│  {                                  │
│    uploaded_files: [                │
│      {file_id: "uuid-1"},           │
│      {file_id: "uuid-2"},           │
│      {file_id: "uuid-3"}            │
│    ]                                │
│  }                                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 7. JavaScript извлекает ID          │
│                                     │
│  const ids = response.uploaded_     │
│    files.map(f => f.file_id);       │
│  // ["uuid-1", "uuid-2", "uuid-3"]  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 8. POST /content/create             │
│                                     │
│  {                                  │
│    title: "...",                    │
│    uploaded_files: [                │
│      "uuid-1",                      │
│      "uuid-2",                      │
│      "uuid-3"                       │
│    ]                                │
│  }                                  │
└─────────────────────────────────────┘
```

---

## ❓ Частые вопросы

### Q: Как браузер передает файлы на сервер?

A: Через `FormData` - специальный объект JavaScript который:
1. Кодирует файлы в `multipart/form-data` формат
2. Автоматически добавляет правильные headers
3. Отправляет бинарные данные файлов

### Q: Почему ключ называется 'files', а не 'file'?

A: Потому что на бэкенде мы делаем `request.files.getlist('files')` - получаем **список** файлов по этому ключу.

Можно использовать любой ключ:
```javascript
formData.append('myfiles', file); // frontend
request.files.getlist('myfiles')  // backend
```

Главное - **одинаковый ключ** на фронте и бэке!

### Q: Можно ли послать массив файлов другим способом?

A: Нет, для файлов **обязательно** использовать `FormData`. Нельзя отправить через `JSON.stringify()` - файлы это бинарные данные, не JSON.

### Q: Что если пользователь не выбрал файлы?

A: Проверяем:
```javascript
if (fileInput.files.length === 0) {
  alert('Выберите файлы');
  return;
}
```

---

## 🎯 Самое главное

**СВЯЗЬ между UI и функцией:**

1. **UI:** `<input type="file">` → пользователь выбирает файлы
2. **JavaScript:** `input.files` → получаем файлы из input
3. **FormData:** `formData.append('files', file)` → упаковываем для отправки
4. **Fetch:** `body: formData` → отправляем на сервер
5. **Результат:** Получаем массив `file_id`
6. **Использование:** Передаем `file_id` в `/content/create`

**Всё! Никакой магии - просто передача данных из формы на сервер!** 🎉

