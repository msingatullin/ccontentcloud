# 📊 API для отображения расхода токенов в ЛК

**Дата:** 20 октября 2025  
**Версия:** 1.0  
**Статус:** ✅ Готово к интеграции

---

## 🎯 Обзор

Система учета токенов позволяет клиентам видеть детальную статистику расхода AI токенов в личном кабинете.

### Что отслеживается:
- Количество токенов (prompt, completion, total)
- Стоимость в рублях и USD
- Расход по агентам
- Расход по AI моделям (GPT-4, GPT-3.5, Claude)
- История по дням для графиков
- Время выполнения запросов

---

## 🔐 Аутентификация

Все endpoints требуют JWT токен в заголовке:
```http
Authorization: Bearer <JWT_TOKEN>
```

---

## 📡 Endpoints

### 1. **Сводка по токенам** (для дашборда)
```http
GET /api/billing/usage/tokens/summary
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "today": {
      "total_tokens": 12500,
      "cost_rub": 15.50,
      "requests_count": 8
    },
    "this_month": {
      "total_tokens": 345000,
      "cost_rub": 428.75,
      "requests_count": 234
    },
    "all_time": {
      "total_tokens": 1250000,
      "cost_rub": 1550.00,
      "requests_count": 890
    }
  }
}
```

**Где использовать:**
- Виджет на главной странице ЛК
- Карточки с быстрой статистикой
- Dashboard Overview

---

### 2. **История по дням** (для графиков)
```http
GET /api/billing/usage/tokens/history?days=30&agent_id=community_concierge
```

**Параметры:**
- `days` (опционально) - количество дней (по умолчанию 30)
- `agent_id` (опционально) - фильтр по агенту

**Ответ:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2025-10-20",
      "total_tokens": 12500,
      "prompt_tokens": 8000,
      "completion_tokens": 4500,
      "cost_rub": 15.50,
      "requests_count": 8
    },
    {
      "date": "2025-10-19",
      "total_tokens": 10200,
      "prompt_tokens": 6500,
      "completion_tokens": 3700,
      "cost_rub": 12.75,
      "requests_count": 6
    }
  ],
  "period": {
    "days": 30,
    "agent_id": "community_concierge"
  }
}
```

**Где использовать:**
- Линейные графики расхода
- Область с заполнением (area chart)
- Сравнение периодов

**Библиотеки для графиков:**
```bash
npm install recharts
# или
npm install chart.js react-chartjs-2
```

**Пример React компонента:**
```jsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

function TokenUsageChart({ days = 30 }) {
  const [data, setData] = useState([]);
  
  useEffect(() => {
    fetch('/api/billing/usage/tokens/history?days=' + days, {
      headers: { 'Authorization': 'Bearer ' + token }
    })
    .then(r => r.json())
    .then(res => setData(res.data));
  }, [days]);
  
  return (
    <LineChart width={800} height={400} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="date" />
      <YAxis />
      <Tooltip />
      <Legend />
      <Line type="monotone" dataKey="total_tokens" stroke="#8884d8" name="Токены" />
      <Line type="monotone" dataKey="cost_rub" stroke="#82ca9d" name="Стоимость ₽" />
    </LineChart>
  );
}
```

---

### 3. **Расход по агентам**
```http
GET /api/billing/usage/tokens/by-agent?period_days=30
```

**Параметры:**
- `period_days` (опционально) - период в днях (по умолчанию 30)

**Ответ:**
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "agent_id": "community_concierge",
        "total_tokens": 125000,
        "cost_rub": 155.50,
        "requests_count": 89,
        "avg_execution_time_ms": 1250
      },
      {
        "agent_id": "multimedia_producer",
        "total_tokens": 98000,
        "cost_rub": 122.00,
        "requests_count": 45,
        "avg_execution_time_ms": 2100
      }
    ],
    "totals": {
      "total_tokens": 345000,
      "total_cost_rub": 428.75,
      "total_requests": 234
    },
    "period_days": 30
  }
}
```

**Где использовать:**
- Круговая диаграмма (pie chart) по агентам
- Таблица с сортировкой
- Рекомендации по оптимизации

**Пример компонента:**
```jsx
function AgentUsageBreakdown() {
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    fetch('/api/billing/usage/tokens/by-agent?period_days=30', {
      headers: { 'Authorization': 'Bearer ' + token }
    })
    .then(r => r.json())
    .then(res => setStats(res.data));
  }, []);
  
  if (!stats) return <Spinner />;
  
  return (
    <div>
      <h3>Расход по агентам за 30 дней</h3>
      <PieChart width={400} height={400}>
        <Pie 
          data={stats.agents} 
          dataKey="cost_rub" 
          nameKey="agent_id" 
          cx="50%" 
          cy="50%" 
          outerRadius={100}
          label
        />
        <Tooltip />
      </PieChart>
      
      <table>
        <thead>
          <tr>
            <th>Агент</th>
            <th>Токены</th>
            <th>Стоимость</th>
            <th>Запросы</th>
          </tr>
        </thead>
        <tbody>
          {stats.agents.map(agent => (
            <tr key={agent.agent_id}>
              <td>{agent.agent_id}</td>
              <td>{agent.total_tokens.toLocaleString()}</td>
              <td>{agent.cost_rub.toFixed(2)} ₽</td>
              <td>{agent.requests_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

### 4. **Расход по AI моделям**
```http
GET /api/billing/usage/tokens/by-model?period_days=30
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "by_model": [
      {
        "ai_provider": "openai",
        "ai_model": "gpt-4",
        "total_tokens": 150000,
        "cost_rub": 250.00,
        "requests_count": 45
      },
      {
        "ai_provider": "openai",
        "ai_model": "gpt-3.5-turbo",
        "total_tokens": 180000,
        "cost_rub": 45.00,
        "requests_count": 189
      },
      {
        "ai_provider": "anthropic",
        "ai_model": "claude-3-sonnet",
        "total_tokens": 15000,
        "cost_rub": 22.50,
        "requests_count": 12
      }
    ],
    "by_provider": [
      {
        "provider": "openai",
        "total_tokens": 330000,
        "total_cost_rub": 295.00,
        "total_requests": 234,
        "models": [...]
      },
      {
        "provider": "anthropic",
        "total_tokens": 15000,
        "total_cost_rub": 22.50,
        "total_requests": 12,
        "models": [...]
      }
    ],
    "period_days": 30
  }
}
```

**Где использовать:**
- Понимание дорогих моделей
- Оптимизация расходов
- Рекомендации по переходу на более дешевые модели

---

### 5. **Детальная таблица** (с пагинацией)
```http
GET /api/billing/usage/tokens/detailed?limit=100&offset=0&agent_id=trends_scout
```

**Параметры:**
- `limit` (опционально) - записей на странице (по умолчанию 100, макс 500)
- `offset` (опционально) - смещение для пагинации
- `agent_id` (опционально) - фильтр по агенту
- `start_date` (опционально) - с даты (ISO формат: 2025-10-01T00:00:00Z)
- `end_date` (опционально) - по дату (ISO формат)

**Ответ:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 12345,
        "agent_id": "trends_scout",
        "ai_provider": "openai",
        "ai_model": "gpt-4",
        "total_tokens": 1250,
        "prompt_tokens": 800,
        "completion_tokens": 450,
        "cost_rub": 1.55,
        "execution_time_ms": 1250,
        "created_at": "2025-10-20T14:30:25Z",
        "content_type": "news_analysis",
        "platform": "telegram"
      }
    ],
    "total": 890,
    "limit": 100,
    "offset": 0,
    "has_more": true
  }
}
```

**Где использовать:**
- Детальная страница с историей
- Таблица с фильтрами
- Экспорт в CSV

**Пример с пагинацией:**
```jsx
function TokenUsageTable() {
  const [data, setData] = useState({ items: [], total: 0 });
  const [page, setPage] = useState(0);
  const limit = 50;
  
  useEffect(() => {
    const offset = page * limit;
    fetch(`/api/billing/usage/tokens/detailed?limit=${limit}&offset=${offset}`, {
      headers: { 'Authorization': 'Bearer ' + token }
    })
    .then(r => r.json())
    .then(res => setData(res.data));
  }, [page]);
  
  return (
    <div>
      <table className="usage-table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Агент</th>
            <th>Модель</th>
            <th>Токены</th>
            <th>Стоимость</th>
            <th>Время</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map(item => (
            <tr key={item.id}>
              <td>{new Date(item.created_at).toLocaleString('ru')}</td>
              <td>{item.agent_id}</td>
              <td>{item.ai_model}</td>
              <td>{item.total_tokens}</td>
              <td>{item.cost_rub.toFixed(2)} ₽</td>
              <td>{item.execution_time_ms}ms</td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <div className="pagination">
        <button 
          disabled={page === 0} 
          onClick={() => setPage(page - 1)}
        >
          Назад
        </button>
        <span>Страница {page + 1} из {Math.ceil(data.total / limit)}</span>
        <button 
          disabled={!data.has_more} 
          onClick={() => setPage(page + 1)}
        >
          Далее
        </button>
      </div>
    </div>
  );
}
```

---

## 🎨 UI/UX рекомендации

### Дашборд (главная страница ЛК)
```jsx
<Dashboard>
  {/* Виджет сводки */}
  <TokenSummaryWidget />
  
  {/* График за 30 дней */}
  <TokenUsageChart days={30} />
  
  {/* Топ-3 агента по расходу */}
  <TopAgentsWidget limit={3} />
</Dashboard>
```

### Страница "Использование токенов"
```jsx
<TokenUsagePage>
  {/* Фильтры */}
  <Filters>
    <DateRangePicker />
    <AgentSelector />
  </Filters>
  
  {/* Графики */}
  <Charts>
    <TokenHistoryChart />
    <AgentBreakdownPie />
    <ModelComparisonBar />
  </Charts>
  
  {/* Детальная таблица */}
  <TokenUsageTable />
</TokenUsagePage>
```

### Цвета и визуализация
```css
/* Цветовая схема */
:root {
  --token-usage-primary: #3b82f6;    /* Синий для токенов */
  --token-usage-cost: #10b981;       /* Зеленый для стоимости */
  --token-usage-warning: #f59e0b;    /* Желтый для предупреждений */
  --token-usage-danger: #ef4444;     /* Красный для превышения лимита */
}

/* Карточка сводки */
.token-summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 24px;
  color: white;
}

.token-count {
  font-size: 32px;
  font-weight: bold;
}

.token-cost {
  font-size: 18px;
  opacity: 0.9;
}
```

---

## 🔧 Интеграция с тарифными планами

Если у тарифных планов будут лимиты по токенам (в будущем), можно добавить индикаторы:

```jsx
function TokenLimitIndicator({ used, limit }) {
  const percentage = (used / limit) * 100;
  const color = percentage > 90 ? 'red' : percentage > 70 ? 'orange' : 'green';
  
  return (
    <div className="token-limit">
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${percentage}%`, backgroundColor: color }}
        />
      </div>
      <p>{used.toLocaleString()} / {limit.toLocaleString()} токенов ({percentage.toFixed(1)}%)</p>
    </div>
  );
}
```

---

## ⚡ Оптимизация производительности

### Кеширование на frontend
```jsx
import { useQuery } from '@tanstack/react-query';

function useTokenSummary() {
  return useQuery({
    queryKey: ['tokenSummary'],
    queryFn: fetchTokenSummary,
    staleTime: 5 * 60 * 1000, // 5 минут кеш
    cacheTime: 30 * 60 * 1000  // 30 минут в памяти
  });
}
```

### Server-Side Rendering (если нужно)
```jsx
// Next.js example
export async function getServerSideProps(context) {
  const summary = await fetchTokenSummary(context.req.headers.authorization);
  
  return {
    props: { summary }
  };
}
```

---

## 🐛 Обработка ошибок

```jsx
function TokenUsageWidget() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetch('/api/billing/usage/tokens/summary', {
      headers: { 'Authorization': 'Bearer ' + token }
    })
    .then(r => {
      if (!r.ok) throw new Error('Failed to fetch');
      return r.json();
    })
    .then(res => {
      setData(res.data);
      setLoading(false);
    })
    .catch(err => {
      setError(err.message);
      setLoading(false);
    });
  }, []);
  
  if (loading) return <Spinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <EmptyState />;
  
  return <TokenSummaryCard data={data} />;
}
```

---

## 📊 Примеры реальных данных

### Для тестирования UI создай моковые данные:
```javascript
export const mockTokenSummary = {
  today: { total_tokens: 12500, cost_rub: 15.50, requests_count: 8 },
  this_month: { total_tokens: 345000, cost_rub: 428.75, requests_count: 234 },
  all_time: { total_tokens: 1250000, cost_rub: 1550.00, requests_count: 890 }
};

export const mockTokenHistory = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  total_tokens: Math.floor(Math.random() * 20000) + 5000,
  prompt_tokens: Math.floor(Math.random() * 12000) + 3000,
  completion_tokens: Math.floor(Math.random() * 8000) + 2000,
  cost_rub: (Math.random() * 25 + 5).toFixed(2),
  requests_count: Math.floor(Math.random() * 15) + 3
})).reverse();
```

---

## 🚀 Развертывание

### 1. Применить миграцию БД
```bash
psql -U postgres -d content_curator < migrations/add_token_usage_indexes.sql
```

### 2. Перезапустить backend
```bash
# Если локально
python app.py

# Если на Cloud Run
gcloud run deploy content-curator --source .
```

### 3. Проверить endpoints
```bash
curl -H "Authorization: Bearer YOUR_JWT" \
  https://your-api.com/api/billing/usage/tokens/summary
```

---

## 📱 Мобильная версия

Все endpoints одинаково работают для web и mobile. Для React Native используй те же запросы:

```jsx
import { useQuery } from '@tanstack/react-query';
import { View, Text } from 'react-native';

function TokenUsageScreen() {
  const { data, isLoading } = useQuery({
    queryKey: ['tokenSummary'],
    queryFn: () => 
      fetch('/api/billing/usage/tokens/summary', {
        headers: { 'Authorization': 'Bearer ' + token }
      }).then(r => r.json())
  });
  
  if (isLoading) return <ActivityIndicator />;
  
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Расход токенов</Text>
      <Text>Сегодня: {data.data.today.total_tokens} токенов</Text>
      <Text>Стоимость: {data.data.today.cost_rub} ₽</Text>
    </View>
  );
}
```

---

## ❓ FAQ для frontend разработчиков

**Q: Как часто обновлять данные?**
A: Сводку (summary) - каждые 5 минут, графики - каждые 15 минут, детальную таблицу - по запросу.

**Q: Нужно ли показывать центы/копейки?**
A: Да, стоимость в рублях показывай с точностью до копеек (2 знака после запятой).

**Q: Какой формат даты использовать?**
A: Backend возвращает ISO 8601 (`2025-10-20T14:30:25Z`). Для отображения используй локаль пользователя:
```js
new Date(item.created_at).toLocaleString('ru-RU')
```

**Q: Как экспортировать в CSV?**
A: Используй endpoint `/detailed` с большим limit и конвертируй в CSV на клиенте или создай отдельный endpoint для экспорта.

---

## 📞 Поддержка

Если нужна помощь с интеграцией, пиши в Telegram или создай issue в репозитории.

---

✅ **Готово к использованию!**

