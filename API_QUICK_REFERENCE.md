# 🚀 API Quick Reference - Шпаргалка

## 📤 Загрузка файлов

| Endpoint | Method | Content-Type | Что делает |
|----------|--------|--------------|------------|
| `/uploads/upload` | POST | `multipart/form-data` | Загрузить файл |
| `/uploads/list` | GET | - | Список файлов |
| `/uploads/{id}` | GET | - | Детали файла |
| `/uploads/{id}` | DELETE | - | Удалить файл |

---

## 📋 Формат данных

### ✅ ПРАВИЛЬНО (массивы)

```json
{
  "business_goals": ["продажи", "подписчики"],
  "keywords": ["AI", "бизнес"],
  "uploaded_files": ["file-id-1", "file-id-2"]
}
```

### ❌ НЕПРАВИЛЬНО (строки)

```json
{
  "business_goals": "продажи. подписчики",
  "keywords": "AI. бизнес",
  "uploaded_files": "file-id-1, file-id-2"
}
```

---

## 🔄 Workflow

```
1. Загрузить файл → получить file.id
2. Добавить file.id в uploaded_files[]
3. Отправить POST /content/create
```

---

## 📏 Лимиты

| Параметр | Значение |
|----------|----------|
| Макс размер файла | 100 MB |
| Макс файлов в запросе | 10 |
| Форматы изображений | jpg, png, gif, webp |
| Форматы документов | pdf, docx, xlsx, md, txt |
| Форматы видео | mp4, mov, avi |

---

## 🎯 Быстрый пример

```javascript
// 1. Загрузить
const formData = new FormData();
formData.append('file', fileObject);
const { file } = await fetch('/uploads/upload', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
}).then(r => r.json());

// 2. Использовать
await fetch('/content/create', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: "Заголовок",
    description: "Описание",
    target_audience: "аудитория",
    business_goals: ["цель1", "цель2"],
    call_to_action: "призыв",
    keywords: ["слово1", "слово2"],
    platforms: ["telegram"],
    uploaded_files: [file.id]  // ← ID файла
  })
});
```

---

## 🔐 Авторизация

Все запросы требуют:
```javascript
headers: {
  'Authorization': `Bearer ${token}`
}
```

---

## 📚 Полная документация

Смотри: `FRONTEND_API_GUIDE.md`

