# ⚡ Electro Bot — Калькулятор электромонтажных работ

Telegram-бот для автоматизированного сбора заявок и предварительного расчёта стоимости электромонтажных работ (квартиры, частные дома). Регион: Ростов-на-Дону.

---

## 🚀 Быстрый старт

### 1. Клонировать / распаковать проект

```bash
cd electro_bot
```

### 2. Создать и активировать виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить переменные окружения

```bash
cp .env.example .env
# Отредактируйте .env — вставьте токен бота, ID администраторов и канала
```

### 5. Запустить

```bash
python main.py
```

---

## ⚙️ Конфигурация `.env`

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен бота из @BotFather |
| `ADMIN_IDS` | Через запятую: `123456789,987654321` |
| `LEADS_CHANNEL_ID` | ID приватного канала: `-1001234567890` |
| `DATABASE_URL` | SQLite: `sqlite+aiosqlite:///bot.db` |

---

## 📁 Структура проекта

```
electro_bot/
├── main.py                  # Точка входа
├── config.py                # Конфигурация и дефолтные цены
├── states.py                # FSM-состояния
├── keyboards.py             # Inline-клавиатуры
├── handlers/
│   ├── user/
│   │   ├── start.py         # /start /help /cancel
│   │   ├── calculator.py    # Основной флоу опроса
│   │   └── confirm.py       # Подтверждение и отправка заявки
│   └── admin/
│       ├── admin_menu.py    # /admin, просмотр, статистика
│       ├── prices.py        # Управление ценами
│       └── coefficients.py  # Управление коэффициентами
├── services/
│   ├── pricing.py           # Логика расчёта стоимости
│   └── lead_sender.py       # Отправка в Telegram-канал
├── database/
│   ├── models.py            # SQLAlchemy-модели
│   └── crud.py              # CRUD + статистика
└── utils/
    ├── validators.py        # Валидация ввода
    └── formatters.py        # Форматирование сообщений
```

---

## 🧮 Логика расчёта

```
base = Σ (кол-во × цена за единицу)
base × коэффициент_вторички × коэффициент_бетона × коэффициент_этажей
min = base × (1 − spread)
max = base × (1 + spread)
```

Все цены и коэффициенты хранятся в таблице `settings` и редактируются через `/admin`.

---

## 👤 Пользовательский флоу

1. `/start` → кнопка «Рассчитать стоимость работ»
2. Выбор типа объекта → тип жилья → площадь → комнаты → материал стен
3. Электрические точки: розетки, выключатели, споты, люстры
4. Дополнительные потребители: плита, духовка, кондей, бойлер, тёплые полы
5. Доп. работы: щит, слаботочка, демонтаж
6. Контакты: имя, телефон, способ связи
7. Итоговый расчёт + «Отправить заявку мастеру»

---

## 🔑 Команды

| Команда | Описание |
|---|---|
| `/start` | Главное меню |
| `/help` | Справка |
| `/cancel` | Отмена текущего опроса |
| `/admin` | Административная панель (только для admin_ids) |

---

## 🚢 Деплой (systemd)

```ini
# /etc/systemd/system/electro_bot.service
[Unit]
Description=Electro Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/electro_bot
ExecStart=/opt/electro_bot/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable electro_bot
sudo systemctl start electro_bot
```
