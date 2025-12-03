# Deployment Instructions

## Переменные окружения для Cloud Run

Для работы Vertex AI необходимо установить следующие переменные окружения в Cloud Run:

```bash
GOOGLE_CLOUD_PROJECT=content-curator-1755119514
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_GEMINI_MODEL=gemini-1.5-pro
VERTEX_AI_IMAGEN_MODEL=imagegeneration@006
```

## Как установить переменные окружения

### Через gcloud CLI:

```bash
gcloud run services update content-curator \
  --set-env-vars GOOGLE_CLOUD_PROJECT=content-curator-1755119514,VERTEX_AI_LOCATION=us-central1,VERTEX_AI_GEMINI_MODEL=gemini-1.5-pro,VERTEX_AI_IMAGEN_MODEL=imagegeneration@006 \
  --region us-central1
```

### Через Cloud Console:

1. Открыть Cloud Run → сервис `content-curator`
2. Edit & Deploy New Revision
3. Variables & Secrets → Add Variable
4. Добавить каждую переменную

## Проверка деплоя

После деплоя проверить логи на наличие строк:
- `🤖 Попытка AI генерации` - значит AI активен
- `✅ Основной контент сгенерирован через AI` - AI работает
- `⚠️ ИСПОЛЬЗУЕТСЯ FALLBACK ГЕНЕРАЦИЯ` - AI не работает, используется fallback

## Troubleshooting

Если контент генерируется плохо:
1. Проверить что переменные окружения установлены
2. Проверить что Service Account имеет роль `roles/aiplatform.user`
3. Проверить логи на наличие ошибок Vertex AI
