# Manual Frontend Deployment Guide
# AI Content Orchestrator Frontend

## 🚀 Ручной деплой на Vercel

### Вариант 1: Vercel Dashboard (Рекомендуется)

#### 1. Подготовка файлов
```bash
# Файлы уже подготовлены:
# - frontend/build/ (production build)
# - frontend/vercel.json (конфигурация)
# - frontend/package.json (зависимости)
```

#### 2. Создание проекта в Vercel
1. Перейти на [vercel.com](https://vercel.com)
2. Войти в аккаунт или создать новый
3. Нажать "New Project"
4. Импортировать GitHub репозиторий или загрузить файлы

#### 3. Настройка проекта
- **Framework Preset**: Create React App
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `build`
- **Install Command**: `npm install`

#### 4. Environment Variables
Добавить в Vercel Dashboard:

```
REACT_APP_API_URL=https://goinvesting.ai
REACT_APP_API_BASE_URL=https://goinvesting.ai/api/v1
REACT_APP_WS_URL=wss://goinvesting.ai/ws
REACT_APP_JWT_STORAGE_KEY=ai_content_orchestrator_token
REACT_APP_REFRESH_TOKEN_KEY=ai_content_orchestrator_refresh_token
REACT_APP_APP_NAME=AI Content Orchestrator
REACT_APP_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=production
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_ERROR_REPORTING=true
REACT_APP_ENABLE_PWA=true
REACT_APP_BILLING_ENABLED=true
REACT_APP_YOOKASSA_SHOP_ID=1134145
REACT_APP_ENABLE_SERVICE_WORKER=true
REACT_APP_CACHE_VERSION=1.0.0
GENERATE_SOURCEMAP=false
REACT_APP_DEBUG=false
```

#### 5. Деплой
1. Нажать "Deploy"
2. Дождаться завершения сборки
3. Получить URL проекта

#### 6. Настройка домена
1. В настройках проекта добавить домен `goinvesting.ai`
2. Настроить DNS записи согласно инструкциям Vercel
3. Включить SSL сертификат

### Вариант 2: Vercel CLI (требует авторизации)

#### 1. Авторизация
```bash
# В папке frontend
npx vercel login
# Следовать инструкциям в браузере
```

#### 2. Деплой
```bash
npx vercel --prod
```

#### 3. Настройка переменных
```bash
npx vercel env add REACT_APP_API_URL
# Ввести: https://goinvesting.ai
# Повторить для всех переменных
```

### Вариант 3: Netlify (Альтернатива)

#### 1. Подготовка
```bash
# Создать netlify.toml в frontend/
echo '[build]
  publish = "build"
  command = "npm run build"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200' > frontend/netlify.toml
```

#### 2. Деплой
1. Перейти на [netlify.com](https://netlify.com)
2. Drag & Drop папку `build` или подключить GitHub
3. Настроить переменные окружения
4. Настроить домен

## 📁 Структура файлов для деплоя

```
frontend/
├── build/                    # Production build (готов к деплою)
│   ├── static/
│   ├── index.html
│   └── manifest.json
├── vercel.json              # Vercel конфигурация
├── package.json             # Зависимости и скрипты
├── public/
│   ├── sw.js               # Service Worker
│   └── manifest.json       # PWA manifest
└── src/                    # Исходный код
```

## 🔧 Проверка после деплоя

### 1. Функциональность
- [ ] Главная страница загружается
- [ ] Навигация работает
- [ ] API запросы проходят
- [ ] Аутентификация работает
- [ ] PWA функции активны

### 2. Performance
- [ ] Lighthouse score > 90
- [ ] Bundle size < 200KB
- [ ] Loading time < 3s
- [ ] Service Worker активен

### 3. Security
- [ ] HTTPS работает
- [ ] Security headers настроены
- [ ] CORS настроен правильно
- [ ] CSP политики активны

## 🚨 Troubleshooting

### Проблемы с деплоем
1. **Build fails**: Проверить зависимости и переменные окружения
2. **404 errors**: Настроить SPA routing в vercel.json
3. **API errors**: Проверить CORS на backend
4. **PWA не работает**: Проверить manifest.json и service worker

### Проблемы с доменом
1. **DNS не работает**: Проверить записи DNS
2. **SSL не активен**: Подождать активации сертификата
3. **Redirects не работают**: Проверить настройки в vercel.json

## 📊 Мониторинг

### Analytics
- Vercel Analytics (встроенный)
- Google Analytics (если настроен)
- Custom events tracking

### Error Monitoring
- Vercel Functions logs
- Browser console errors
- Service Worker errors

## 🔄 Обновления

### Автоматические (GitHub integration)
1. Push в main branch
2. Vercel автоматически деплоит
3. Проверить результат

### Ручные
1. Изменить код
2. `npm run build`
3. Загрузить новую версию в Vercel

---

## ✅ Checklist для деплоя

- [ ] Production build создан
- [ ] Vercel проект создан
- [ ] Environment variables настроены
- [ ] Домен добавлен
- [ ] DNS записи настроены
- [ ] SSL сертификат активен
- [ ] Функциональность проверена
- [ ] Performance проверена
- [ ] Security проверена
- [ ] Мониторинг настроен

**🎯 Frontend готов к production деплою!**

Все файлы подготовлены, конфигурация настроена. Выберите удобный способ деплоя и следуйте инструкциям выше.
