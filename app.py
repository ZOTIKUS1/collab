import json
import os
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Конфигурация
TOKEN = "7601732852:AAGb4aUH7YGVcJaqy3ZgDNHCyY2Hb-t76uU"
ADMIN_ID = 985345893  # Ваш ID в Telegram
WELCOME_IMAGE_PATH = "welcome.png"  # Путь к изображению приветствия

# Файлы данных
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CONNECTIONS_FILE = os.path.join(DATA_DIR, "connections.json")
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")

# Создаем папку для данных, если её нет
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def load_data(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def main_menu_keyboard():
    return ReplyKeyboardMarkup([
        ["🔍 Найти партнеров", "🌍 Глобальный поиск"],
        ["👤 Мой профиль", "✏️ Редактировать профиль"]
    ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Пытаемся отправить фото с приветствием
        if os.path.exists(WELCOME_IMAGE_PATH):
            with open(WELCOME_IMAGE_PATH, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=update.message.chat_id,
                    photo=InputFile(photo),
                    caption="<b>🌟 Добро пожаловать в CollabLeaks! 🌟</b>\n\n"
                            "Этот бот создан для профессиональных знакомств и деловых контактов.\n\n"
                            "<b>📌 Основные возможности:</b>\n"
                            "• Создание профессионального профиля\n"
                            "• Поиск партнеров по отраслям и городам\n"
                            "• Безопасный обмен контактами\n"
                            "• Система жалоб и модерация\n\n"
                            "Чтобы начать, нажмите /register",
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text(
                "<b>🌟 Добро пожаловать в Professional Connect! 🌟</b>\n\n"
                "Этот бот создан для профессиональных знакомств и деловых контактов.\n\n"
                "<b>📌 Основные возможности:</b>\n"
                "• Создание профессионального профиля\n"
                "• Поиск партнеров по отраслям и городам\n"
                "• Безопасный обмен контактами\n"
                "• Система жалоб и модерация\n\n"
                "Чтобы начать, нажмите /register",
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Ошибка при отправке приветствия: {e}")
        await update.message.reply_text(
            "Добро пожаловать! Используйте /register для создания профиля."
        )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    users = load_data(USERS_FILE)

    if user_id in users:
        await update.message.reply_text(
            "Вы уже зарегистрированы!",
            reply_markup=main_menu_keyboard()
        )
        return

    users[user_id] = {
        "name": update.message.from_user.full_name,
        "username": update.message.from_user.username,
        "city": "",
        "industry": "",
        "skills": "",
        "bio": "",
        "photo": None,
        "reports": 0,
        "banned": False
    }
    save_data(USERS_FILE, users)

    await update.message.reply_text(
        "Давайте создадим ваш профессиональный профиль.\n\n"
        "Из какого вы города?",
        reply_markup=ReplyKeyboardMarkup([["Отменить"]], resize_keyboard=True)
    )
    context.user_data["step"] = "city"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    users = load_data(USERS_FILE)

    # Обработка команд главного меню
    if text == "🔍 Найти партнеров":
        await show_next_partner(user_id, context, local=True)
        return
    elif text == "🌍 Глобальный поиск":
        await show_next_partner(user_id, context, local=False)
        return
    elif text == "👤 Мой профиль":
        await show_profile(update, context)
        return
    elif text == "✏️ Редактировать профиль":
        await edit_profile_options(update, context)
        return
    elif text == "Отменить":
        await update.message.reply_text(
            "Действие отменено",
            reply_markup=main_menu_keyboard()
        )
        if "step" in context.user_data:
            del context.user_data["step"]
        return

    # Обработка шагов регистрации
    if user_id not in users or "step" not in context.user_data:
        return

    step = context.user_data["step"]

    if step == "city":
        users[user_id]["city"] = text
        context.user_data["step"] = "industry"
        save_data(USERS_FILE, users)
        await update.message.reply_text(
            "В какой отрасли вы работаете? (IT, Маркетинг, Финансы и т.д.)",
            reply_markup=ReplyKeyboardMarkup([["Отменить"]], resize_keyboard=True)
        )

    elif step == "industry":
        users[user_id]["industry"] = text
        context.user_data["step"] = "skills"
        save_data(USERS_FILE, users)
        await update.message.reply_text(
            "Перечислите ваши ключевые навыки через запятую:",
            reply_markup=ReplyKeyboardMarkup([["Отменить"]], resize_keyboard=True)
        )

    elif step == "skills":
        users[user_id]["skills"] = text
        context.user_data["step"] = "bio"
        save_data(USERS_FILE, users)
        await update.message.reply_text(
            "Напишите краткое профессиональное резюме (3-5 предложений):",
            reply_markup=ReplyKeyboardMarkup([["Отменить"]], resize_keyboard=True)
        )

    elif step == "bio":
        users[user_id]["bio"] = text
        context.user_data["step"] = "photo"
        save_data(USERS_FILE, users)
        await update.message.reply_text(
            "Отправьте ваше профессиональное фото (по желанию) или нажмите 'Пропустить':",
            reply_markup=ReplyKeyboardMarkup([["Пропустить", "Отменить"]], resize_keyboard=True)
        )

    elif step == "photo":
        if text == "Пропустить":
            users[user_id]["photo"] = None
            save_data(USERS_FILE, users)
            del context.user_data["step"]
            await update.message.reply_text(
                "✅ Профиль успешно создан!",
                reply_markup=main_menu_keyboard()
            )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    users = load_data(USERS_FILE)

    if user_id not in users or "step" not in context.user_data or context.user_data["step"] != "photo":
        return

    photo = update.message.photo[-1].file_id
    users[user_id]["photo"] = photo
    save_data(USERS_FILE, users)
    del context.user_data["step"]
    await update.message.reply_text(
        "✅ Профиль успешно создан!",
        reply_markup=main_menu_keyboard()
    )


async def show_next_partner(user_id: str, context: ContextTypes.DEFAULT_TYPE, local: bool = True):
    users = load_data(USERS_FILE)
    connections = load_data(CONNECTIONS_FILE)
    reports = load_data(REPORTS_FILE)

    current_user = users.get(user_id, {})
    current_city = current_user.get("city", "")

    available_users = [
        uid for uid, data in users.items()
        if (uid != user_id and
            not data.get("banned", False) and
            uid not in connections.get(user_id, []) and
            data.get("reports", 0) < 3 and
            (not local or data.get("city") == current_city))
    ]

    if not available_users:
        mode = "вашем городе" if local else "глобальном поиске"
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🚫 Нет новых профилей в {mode}.",
            reply_markup=main_menu_keyboard()
        )
        return

    target_id = available_users[0]
    target = users[target_id]

    keyboard = [
        [
            InlineKeyboardButton("👍 Заинтересован", callback_data=f"connect_{target_id}"),
            InlineKeyboardButton("➡️ Следующий", callback_data=f"next_{int(local)}")
        ],
        [InlineKeyboardButton("❌ Пожаловаться", callback_data=f"report_{target_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    city_info = f"\n🏙 Город: {target.get('city', 'не указан')}" if local else ""

    caption = (
        f"👤 <b>{target['name']}</b>{city_info}\n"
        f"🏢 Отрасль: {target['industry']}\n"
        f"🛠 Навыки: {target['skills']}\n"
        f"📝 О себе:\n{target['bio']}"
    )

    if target["photo"]:
        await context.bot.send_photo(
            chat_id=user_id,
            photo=target["photo"],
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    users = load_data(USERS_FILE)

    if user_id not in users:
        await update.message.reply_text(
            "Сначала создайте профиль командой /register",
            reply_markup=main_menu_keyboard()
        )
        return

    user = users[user_id]

    text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"<b>Имя:</b> {user['name']}\n"
        f"<b>Город:</b> {user.get('city', 'не указан')}\n"
        f"<b>Отрасль:</b> {user['industry']}\n"
        f"<b>Навыки:</b> {user['skills']}\n\n"
        f"<b>О себе:</b>\n{user['bio']}"
    )

    if user["photo"]:
        await update.message.reply_photo(
            user["photo"],
            caption=text,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )


async def edit_profile_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Город", callback_data="edit_city"),
         InlineKeyboardButton("Отрасль", callback_data="edit_industry")],
        [InlineKeyboardButton("Навыки", callback_data="edit_skills"),
         InlineKeyboardButton("Описание", callback_data="edit_bio")],
        [InlineKeyboardButton("Фото", callback_data="edit_photo")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✏️ <b>Редактирование профиля</b>\nВыберите что изменить:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = str(query.from_user.id)
    users = load_data(USERS_FILE)
    connections = load_data(CONNECTIONS_FILE)
    reports = load_data(REPORTS_FILE)

    if data.startswith("next_"):
        is_local = bool(int(data.split("_")[1]))
        await query.delete_message()
        await show_next_partner(user_id, context, local=is_local)

    elif data == "back_to_menu":
        await query.delete_message()
        await context.bot.send_message(
            chat_id=user_id,
            text="Главное меню:",
            reply_markup=main_menu_keyboard()
        )

    elif data.startswith("connect_"):
        target_id = data.split("_")[1]

        # Добавляем соединение
        if user_id not in connections:
            connections[user_id] = []
        connections[user_id].append(target_id)
        save_data(CONNECTIONS_FILE, connections)

        # Уведомляем цель
        target = users[target_id]
        await context.bot.send_message(
            chat_id=target_id,
            text=f"💌 <b>Новый интерес к вашему профилю!</b>\n\n"
                 f"Пользователь: {users[user_id]['name']}\n"
                 f"Город: {users[user_id].get('city', 'не указан')}\n"
                 f"Отрасль: {users[user_id]['industry']}\n\n"
                 f"Используйте поиск, чтобы найти этого пользователя.",
            parse_mode="HTML"
        )

        # Проверка взаимного интереса
        if target_id in connections and user_id in connections[target_id]:
            user = users[user_id]

            # Уведомление инициатору
            contact_msg = f"@{target['username']}" if target.get(
                'username') else f"<a href='tg://user?id={target_id}'>написать сообщение</a>"
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🤝 <b>Взаимный интерес!</b>\n\n"
                     f"{target['name']} тоже заинтересован(а) в сотрудничестве.\n\n"
                     f"Контакт: {contact_msg}",
                parse_mode="HTML"
            )

            # Уведомление цели
            contact_msg = f"@{user['username']}" if user.get(
                'username') else f"<a href='tg://user?id={user_id}'>написать сообщение</a>"
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🤝 <b>Взаимный интерес!</b>\n\n"
                     f"{user['name']} тоже заинтересован(а) в сотрудничестве.\n\n"
                     f"Контакт: {contact_msg}",
                parse_mode="HTML"
            )

        await query.delete_message()
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Ваш интерес зарегистрирован!",
            reply_markup=main_menu_keyboard()
        )

    elif data.startswith("report_"):
        target_id = data.split("_")[1]

        # Регистрируем жалобу
        if target_id not in reports:
            reports[target_id] = []

        if user_id not in reports[target_id]:
            reports[target_id].append(user_id)
            users[target_id]["reports"] = len(reports[target_id])

            # Автобан при 3+ жалобах
            if users[target_id]["reports"] >= 3:
                users[target_id]["banned"] = True
                await context.bot.send_message(
                    chat_id=target_id,
                    text="🚫 Ваш профиль был заблокирован из-за многочисленных жалоб."
                )

            save_data(REPORTS_FILE, reports)
            save_data(USERS_FILE, users)

            # Уведомление администратору
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ <b>Новая жалоба</b>\n\n"
                     f"На пользователя: {users[target_id]['name']}\n"
                     f"ID: {target_id}\n"
                     f"Город: {users[target_id].get('city', 'не указан')}\n"
                     f"Всего жалоб: {users[target_id]['reports']}\n\n"
                     f"Для просмотра: /inspect_{target_id}",
                parse_mode="HTML"
            )

            await query.answer("✅ Жалоба отправлена администратору")
        else:
            await query.answer("Вы уже жаловались на этого пользователя")

        await query.delete_message()
        await context.bot.send_message(
            chat_id=user_id,
            text="Спасибо за вашу бдительность!",
            reply_markup=main_menu_keyboard()
        )

    elif data.startswith("edit_"):
        field = data.split("_")[1]
        context.user_data["editing"] = field
        await query.edit_message_text(
            f"✏️ Введите новое значение для {field}:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Отменить", callback_data="back_to_menu")]
            ])
        )


# Команды для администратора
async def show_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    reports = load_data(REPORTS_FILE)
    users = load_data(USERS_FILE)

    text = "📋 <b>Список жалоб</b>\n\n"
    for reported_id, reporter_ids in reports.items():
        user = users.get(reported_id, {"name": "Неизвестный", "city": ""})
        text += f"👤 <b>{user['name']}</b> (ID: {reported_id})\n"
        text += f"🏙 Город: {user.get('city', 'не указан')}\n"
        text += f"⚠️ Жалоб: {len(reporter_ids)}\n"
        text += f"🔍 /inspect_{reported_id}\n\n"

    await update.message.reply_text(
        text or "ℹ️ Жалоб пока нет",
        parse_mode="HTML"
    )


async def inspect_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    try:
        target_id = context.args[0]
    except IndexError:
        await update.message.reply_text("Используйте: /inspect USER_ID")
        return

    users = load_data(USERS_FILE)
    reports = load_data(REPORTS_FILE)

    user = users.get(target_id, {})

    text = "🔍 <b>Информация о пользователе</b>\n\n"
    text += f"ID: {target_id}\n"
    text += f"Имя: {user.get('name', 'Неизвестный')}\n"
    text += f"Город: {user.get('city', 'не указан')}\n"
    text += f"Отрасль: {user.get('industry', 'не указана')}\n"
    text += f"Статус: {'🚫 Заблокирован' if user.get('banned') else '✅ Активен'}\n"
    text += f"Жалоб: {len(reports.get(target_id, []))}\n\n"

    if target_id in reports:
        text += "Последние 3 жалобы от:\n"
        for reporter_id in reports[target_id][-3:]:
            reporter = users.get(reporter_id, {"name": "Неизвестный"})
            text += f"- {reporter['name']} (ID: {reporter_id})\n"

    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )


def main():
    app = Application.builder().token(TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("reports", show_reports))
    app.add_handler(CommandHandler("inspect", inspect_user))

    # Обработчики сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Обработчики кнопок
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()