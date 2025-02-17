import asyncio
from aiogram import F
from aiogram import Bot, Dispatcher, types, BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import platform
import requests
from datetime import datetime
import logging
from data import config
from database import db

# Конфигурация
SCRIPT_DIR = config.LOG_DIR
ITEMS_PER_PAGE = 5

token = config.BOT_TOKEN
bot = Bot(token=token)
dp = Dispatcher()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(SCRIPT_DIR / 'start.log', encoding='utf-8')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logging.getLogger("aiogram.event").setLevel(logging.WARNING)


class States(StatesGroup):
    already_started = State()
    adding_item = State()
    deleting_item = State()
    viewing_wishlists = State()
    adding_friend = State()


if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def check_link_liquidity(link):
    try:
        if link.startswith("https://"):
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False


async def set_default_keyboard(chat_id):
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="/мой_вишлист"),
                types.KeyboardButton(text="/друзья"))
    builder.row(types.KeyboardButton(text="/добавить"),
                types.KeyboardButton(text="/удалить"))
    builder.row(types.KeyboardButton(text="/добавить_друга"))
    await bot.send_message(chat_id, "Выберите действие:", reply_markup=builder.as_markup(resize_keyboard=True))


@dp.message(StateFilter(default_state, States.already_started), Command(commands=["start"]))
async def start_handler(message: Message, state: FSMContext):
    if not message.from_user.username:
        await bot.send_message(message.chat.id, "Для использования этого бота вам необходимо иметь юзернейм для Телеграма!\nНастроить его можно в настройках профиля")
        return
    await state.set_state(States.already_started)
    users_list = [i[0] for i in await db.fetch_all("SELECT id FROM users")]
    if message.from_user.id not in users_list:
        await db.execute(
            "INSERT INTO users (id, username) VALUES (%s, %s)",
            (message.from_user.id, message.from_user.username))
        await db.execute(
            f"CREATE TABLE {message.from_user.username} (stuff_link VARCHAR(2048))")

        await bot.send_message(message.from_user.id, f"Привет, {message.from_user.username}! Ваш вишлист создан.")
    else:
        await bot.send_message(message.from_user.id, f"Привет, {message.from_user.username}! Что хочешь сделать?")
    await set_default_keyboard(message.from_user.id)


@dp.message(StateFilter(States.already_started), Command(commands=["добавить"]))
async def add_item_handler(message: Message, state: FSMContext):
    await state.set_state(States.adding_item)
    await bot.send_message(message.from_user.id, "Отправьте сюда ссылку на товар без лишних символов или введите 0 для выхода:")


@dp.message(StateFilter(States.adding_item))
async def adding_item(message: Message, state: FSMContext):
    item_link = message.text
    goods = [i[0] for i in await db.fetch_all(f"SELECT stuff_link FROM {message.from_user.username.lower()}")]
    if item_link == "0":
        await state.set_state(States.already_started)
        await set_default_keyboard(message.from_user.id)
        return
    if await check_link_liquidity(item_link):
        if item_link in goods:
            await bot.send_message(message.from_user.id, "Ошибка: ссылка уже есть в вашем списке. Попробуйте другую")
            return
        await db.execute(f"INSERT INTO {message.from_user.username.lower()} VALUES (%s)",
                         (item_link, ))
        await bot.send_message(message.from_user.id, f"Товар добавлен в ваш список.")
        await state.set_state(States.already_started)
        await set_default_keyboard(message.from_user.id)
    else:
        await bot.send_message(message.from_user.id, "Ошибка: ссылка не найдена или недоступна. Попробуйте еще раз")


@dp.callback_query(F.data.startswith("del_"), StateFilter(States.deleting_item))
async def delete_item(callback_query: CallbackQuery):
    try:
        # Получаем индекс товара из callback_data
        item_index = int(callback_query.data.replace("del_", ""))

        # Получаем данные пользователя
        username = callback_query.from_user.username

        wishes = [i[0] for i in await db.fetch_all(f"SELECT stuff_link FROM {username.lower()}")]

        # Удаляем товар по индексу
        if 0 <= item_index < len(wishes):
            await db.execute(f"DELETE FROM {username.lower()} WHERE stuff_link = %s", (wishes[item_index], ))

            await callback_query.answer("Товар удален")
            await callback_query.message.delete()
        else:
            await callback_query.answer("Товар не найден")

    except Exception as e:
        await callback_query.answer("Произошла ошибка при удалении")
        logger.error(f"Error with deleting: {e}")


@dp.callback_query(F.data == "stop_deleting", StateFilter(States.deleting_item))
async def stop_deleting(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.delete()
    await bot.send_message(callback_query.from_user.id, "Удаление товаров остановлено.")
    await state.set_state(States.already_started)
    await set_default_keyboard(callback_query.from_user.id)


@dp.message(StateFilter(States.already_started), Command(commands=["удалить"]))
async def deleting_item_handler(message: Message, state: FSMContext):
    await state.set_state(States.deleting_item)

    try:
        wishes = [i[0] for i in await db.fetch_all(f"SELECT stuff_link FROM {message.from_user.username.lower()}")]

        if not wishes:
            await bot.send_message(message.from_user.id, "Ваш вишлист пуст.")
            await state.set_state(States.already_started)
            await set_default_keyboard(message.from_user.id)
            return
        # Отправляем каждый товар с кнопкой удаления
        for index, item in enumerate(wishes):
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text="Удалить",
                callback_data=f"del_{index}"
            ))
            await bot.send_message(message.from_user.id, item, reply_markup=builder.as_markup())

        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text="Закончить",
            callback_data="stop_deleting"
        ))
        await bot.send_message(
            message.from_user.id,
            "Для завершения нажмите:",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        await bot.send_message(
            message.from_user.id,
            "Произошла ошибка при загрузке списка товаров."
        )
        logger.error(f"Error with wishlist uploading: {e}")
        await state.set_state(States.already_started)
        await set_default_keyboard(message.from_user.id)


@dp.message(StateFilter(States.already_started), Command(commands=['мой_вишлист']))
async def my_wishlist_handler(message: Message):
    wishlist = [i[0] for i in await db.fetch_all(
        f"SELECT * FROM {message.from_user.username.lower()}")]
    if not wishlist:
        await bot.send_message(message.from_user.id, "Ваш вишлист пуст.")
        await set_default_keyboard(message.from_user.id)
        return
    await bot.send_message(message.from_user.id, "Ваш вишлист:")
    for link in wishlist:
        await bot.send_message(message.from_user.id, link)

# Команда /friends


@dp.message(StateFilter(States.already_started), Command(commands=['друзья']))
async def cmd_friends(message: Message):
    # Отправляем первую страницу
    await show_friends_page(message, user_id=message.from_user.id, page=0)


async def show_friends_page(message: types.Message, user_id: int, page: int):
    friends = [
        i[0] if i[1] == user_id else i[1]
        for i in await db.fetch_all(
            "SELECT user_1, user_2 FROM friends_list WHERE (user_1 = %s OR user_2 = %s) AND status = 'accepted' LIMIT %s OFFSET %s",
            (user_id, user_id, ITEMS_PER_PAGE, page * ITEMS_PER_PAGE))
    ]

    # Получаем общее количество друзей
    total_friends = (await db.fetch_one(
        "SELECT COUNT(*) FROM friends_list WHERE user_1 = %s OR user_2 = %s",
        (user_id, user_id)
    ))[0]

    # Создаем клавиатуру с кнопками для друзей
    builder = InlineKeyboardBuilder()
    for friend in friends:
        friend_name = (await db.fetch_one("SELECT username FROM users WHERE id = %s", (friend, )))[0]
        builder.add(types.InlineKeyboardButton(
            text=friend_name, callback_data=f"friend_{friend}"))

    # Добавляем кнопки для навигации
    if page > 0:
        builder.add(types.InlineKeyboardButton(
            text="Назад", callback_data=f"page_{page - 1}"))
    if (page + 1) * ITEMS_PER_PAGE < total_friends:
        builder.add(types.InlineKeyboardButton(
            text="Вперед", callback_data=f"page_{page + 1}"))

    # Отправляем сообщение с кнопками
    await message.answer(f"Страница {page + 1}. Выберите друга:", reply_markup=builder.as_markup())

# Обработка нажатия на кнопку с другом


@dp.callback_query(F.data.startswith("friend_"))
async def process_friend_selection(callback_query: types.CallbackQuery):
    friend_id = int(callback_query.data.split("_")[1])

    friend_name = (await db.fetch_one("SELECT username FROM users WHERE id = %s", (friend_id, )))[0]

    wishes = [i[0] for i in await db.fetch_all(
        f"SELECT * FROM {friend_name.lower()}")]

    if not wishes:
        await bot.send_message(callback_query.from_user.id, f"Вишлист @{friend_name} пуст.")
        await set_default_keyboard(callback_query.from_user.id)
        return
    await bot.send_message(callback_query.from_user.id, f"Вишлист @{friend_name}:")
    for link in wishes:
        await bot.send_message(callback_query.from_user.id, link)

    # Подтверждаем обработку callback
    await callback_query.answer()

# Обработка нажатия на кнопку пагинации


@dp.callback_query(F.data.startswith("page_"))
async def process_page_selection(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split("_")[1])
    await show_friends_page(callback_query.message, user_id=callback_query.from_user.id, page=page)
    await callback_query.answer()


@dp.message(StateFilter(States.already_started), Command(commands=["добавить_друга"]))
async def add_friend_handler(message: Message, state: FSMContext):
    await state.set_state(States.adding_friend)
    await bot.send_message(message.chat.id, "Чтобы добавить друга, отправьте его юзернейм в формате @username или 0, чтобы завершить процесс:")


@dp.message(StateFilter(States.adding_friend))
async def adding_friend(message: Message, state: FSMContext):
    if message.text == '0':
        await bot.send_message(message.chat.id, "Добавление друга завершено.")
        await state.set_state(States.already_started)
        await set_default_keyboard(message.chat.id)
        return
    if message.text.startswith("@"):
        username = message.text.replace("@", "")
        users_list = [i[0] for i in await db.fetch_all("SELECT username FROM users")]
        if username in users_list:
            friend_id = (await db.fetch_one("SELECT id FROM users WHERE username = %s", (username, )))[0]
            if friend_id == message.from_user.id:
                await bot.send_message(message.chat.id, "Вы не можете добавить себя в друзья.")
                return
            user1 = message.from_user.id
            user2 = friend_id
            old_request = (await db.fetch_one("SELECT status, time FROM friends_list WHERE user_1 IN (%s, %s) AND user_2 IN (%s, %s)", (user1, user2, user1, user2)))
            if old_request:
                if old_request[0] == 'accepted':
                    await bot.send_message(message.chat.id, f"Вы уже друзья с {message.text}. Попробуйте другой юзернейм")
                    return
                if old_request[0] == 'waiting' or old_request[0] == 'rejected':
                    old_time = old_request[1]
                    if (datetime.now() - old_time).total_seconds() // 60 < 5:
                        await bot.send_message(message.chat.id, f"Предыдущий запрос {message.text} был отправлен менее 5 минут. Попробуйте позже.")
                        return
                    else:
                        await db.execute("DELETE FROM friends_list WHERE user_1 IN (%s, %s) AND user_2 IN (%s, %s)", (user1, user2, user1, user2))
            await db.execute("INSERT INTO friends_list VALUES(%s, %s, 'waiting', %s)", (user1, user2, datetime.now()))
            await bot.send_message(message.chat.id, f"Запрос дружбы отправлен {message.text}")
            await state.set_state(States.already_started)
            await set_default_keyboard(message.chat.id)
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text="Принять",
                callback_data=f"accept_friend^{user1}",
            ))
            builder.add(types.InlineKeyboardButton(
                text="Отклонить",
                callback_data=f"reject_friend^{user1}",
            ))
            await bot.send_message(friend_id, f"@{message.from_user.username} хочет добавить вас в друзья. Принять заявку?", reply_markup=builder.as_markup())
        else:
            await bot.send_message(message.chat.id, f"Пользователь {message.text} не найден.")
    else:
        await bot.send_message(message.chat.id, "Введен неверный юзернейм. Формат юзернейма @username или 0 для завершения.")


@dp.callback_query(F.data.startswith("accept_friend"), StateFilter(States.already_started))
async def accept_friend(callback_query: CallbackQuery):
    friend_id = callback_query.data.split('^')[1]
    user_id = callback_query.from_user.id
    friend_name = (await db.fetch_one("SELECT username FROM users WHERE id = %s", (friend_id, )))[0]
    await callback_query.answer()
    await bot.send_message(int(friend_id), f"@{callback_query.from_user.username} принял ваш запрос дружбы.")
    await bot.send_message(int(user_id), f"Вы добавили @{friend_name} в друзья.")
    await db.execute("UPDATE friends_list SET status = 'accepted' WHERE user_1 IN (%s, %s) AND user_2 IN (%s, %s)", (user_id, friend_id, user_id, friend_id))


@dp.callback_query(F.data.startswith("reject_friend"), StateFilter(States.already_started))
async def reject_friend(callback_query: CallbackQuery):
    friend_id = callback_query.data.split('^')[1]
    user_id = callback_query.from_user.id
    await callback_query.answer()
    await bot.send_message(int(friend_id), f"@{callback_query.from_user.username} отклонил ваш запрос дружбы.")
    await bot.send_message(int(user_id), "Запрос отклонен")
    await db.execute("UPDATE friends_list SET status = 'rejected' WHERE user_1 IN (%s, %s) AND user_2 IN (%s, %s)", (user_id, friend_id, user_id, friend_id,))


async def on_shutdown():
    logger.info("Starting bot shutdown...")
    try:
        await bot.session.close()
        logger.info("Bot session was closed successfully")
        await db.close()
    except Exception as e:
        logger.info(f"Error with bot session closig: {e}")

    logger.info("Shutdown completed successfully")


async def main():
    logger.info("Bot starting...")

    try:
        logger.info("Polling starting...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Critical error: {e}")
        raise
    finally:
        await on_shutdown()
        logger.info("Bot is stopped")

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Exit is caught...")
    except Exception as e:
        logger.error(f"Uncaught error: {e}")
    finally:
        try:
            tasks = asyncio.all_tasks(loop)
            for task in tasks:
                task.cancel()
            if tasks:
                loop.run_until_complete(asyncio.gather(
                    *tasks, return_exceptions=True))
            loop.close()
        except Exception as e:
            logger.error(f"Error with loop closing: {e}")
        logger.info("Program is fiished")
