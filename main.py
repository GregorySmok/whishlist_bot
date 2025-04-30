import asyncio
from typing import Callable, Dict, Any, Awaitable
from aiogram import F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types, BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from emoji import emojize
from aiogram.dispatcher.event.bases import CancelHandler
import platform
import requests
from datetime import datetime
import traceback
import config
from database import db
from logging_setup import main_logger, log_user_action, log_error

ITEMS_PER_PAGE = 3
token = config.BOT_TOKEN
bot = Bot(token=token)
dp = Dispatcher(storage=MemoryStorage())


class States(StatesGroup):
    already_started = State()
    adding_item = State()
    deleting_item = State()
    viewing_wishlists = State()
    admin = State()


class BanMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Проверяем, находится ли пользователь в бан-листе
        user_id = event.from_user.username

        # Здесь выполняем запрос к базе данных для проверки
        is_banned = await self.check_if_banned(user_id)

        if is_banned:
            # Если пользователь в бан-листе, прерываем обработку
            # Можно также отправить сообщение о том, что пользователь заблокирован
            await event.answer("Вы заблокированы")
            raise CancelHandler()

        # Если пользователь не в бан-листе, продолжаем обработку
        return await handler(event, data)

    async def check_if_banned(self, user_id: str) -> bool:
        result = await db.fetch_one(
            "SELECT * FROM banlist WHERE username = %s", (user_id,)
        )
        return result


if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def check_link_liquidity(link):
    try:
        if link.startswith("https://"):
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        log_error("system", f"Error checking link: {e}")
        return False


async def set_default_keyboard(chat_id):
    try:
        builder = ReplyKeyboardBuilder()
        builder.row(
            types.KeyboardButton(text="/мой_вишлист"),
            types.KeyboardButton(text="/друзья"),
        )
        builder.row(
            types.KeyboardButton(text="/добавить"),
            types.KeyboardButton(text="/удалить"),
        )
        builder.row(types.KeyboardButton(
            text="/добавить_друга", request_user=types.KeyboardButtonRequestUser(request_id=1, user_is_bot=False)))
        await bot.send_message(
            chat_id,
            "Выберите действие:",
            reply_markup=builder.as_markup(resize_keyboard=True),
        )
    except Exception as e:
        log_error(
            chat_id, f"Error setting default keyboard: {e}", traceback.format_exc(
            )
        )
        await bot.send_message(
            chat_id,
            "Произошла ошибка при настройке клавиатуры. Пожалуйста, попробуйте позже или используйте текстовые команды.",
        )


async def set_admin_keyboard(chat_id):
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="/users"),
                types.KeyboardButton(text="/banlist"))
    builder.row(
        types.KeyboardButton(text="/close"),
    )
    await bot.send_message(
        chat_id,
        "Admin panel activated",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


@dp.message(StateFilter(States.already_started), Command(commands=["admin"]))
async def admin_handler(message: Message, state: FSMContext):
    if message.chat.id in config.admins:
        await state.set_state(States.admin)
        await set_admin_keyboard(message.chat.id)


@dp.message(StateFilter(States.admin), Command(commands=["users"]))
async def get_users(message: Message):
    users = [i[0] for i in await db.fetch_all("SELECT username FROM users")]
    text = "Пользователи:\n"
    for num, user in enumerate(users):
        text += f"{num + 1}. @{user}\n"
    await bot.send_message(message.chat.id, text)


@dp.message(StateFilter(States.admin), Command(commands=["banlist"]))
async def get_banlist(message: Message):
    users = [i[0] for i in await db.fetch_all("SELECT username FROM banlist")]
    text = "Заблокированные пользователи:\n"
    for num, user in enumerate(users):
        text += f"{num + 1}. @{user}\n"
    await bot.send_message(message.chat.id, text)


@dp.message(StateFilter(States.admin), Command(commands=["ban"]))
async def ban_handler(message: Message):
    user = message.text.split()[1]
    try:
        await db.execute("INSERT INTO banlist (username) VALUES (%s)", (user,))
        await bot.send_message(
            message.chat.id, f"Пользователь @{user} успешно заблокирован.")
    except:
        await bot.send_message("Не удалось заблокировать этого пользователя")


@dp.message(StateFilter(States.admin), Command(commands=["unban"]))
async def unban_handler(message: Message):
    user = message.text.split()[1]
    try:
        await db.execute("DELETE FROM banlist WHERE username = %s", (user,))
        await bot.send_message(
            message.chat.id, f"Пользователь @{user} успешно разблокирован")
    except:
        await bot.send_message("Не удалось разблокировать этого пользователя")


@dp.message(StateFilter(States.admin), Command(commands=["notification"]))
async def notify_handler(message: Message):
    text = " ".join(message.text.split()[1:])
    users = [i[0] for i in await db.fetch_all("SELECT id FROM users")]
    for user in users:
        try:
            await bot.send_message(user, text)
        except Exception as e:
            log_error(
                message.from_user.id,
                f"Error sending notification: {e}",
                traceback.format_exc(),
            )


@dp.message(StateFilter(States.admin), Command(commands=["close"]))
async def close_handler(message: Message, state: FSMContext):
    await state.set_state(States.already_started)
    await set_default_keyboard(message.chat.id)


@dp.message(
    StateFilter(default_state, States.already_started), Command(
        commands=["start"])
)
async def start_handler(message: Message, state: FSMContext):
    try:
        if not message.from_user.username:
            await bot.send_message(
                message.chat.id,
                "Для использования этого бота вам необходимо иметь юзернейм для Телеграма!\nНастроить его можно в настройках профиля",
            )
            log_user_action(
                message.from_user.id,
                "no_username",
                "start_attempt",
                "User without username attempted to start bot",
            )
            return

        await state.set_state(States.already_started)
        users_list = [i[0] for i in await db.fetch_all("SELECT id FROM users")]

        if message.from_user.id not in users_list:
            await db.execute(
                "INSERT INTO users (id, username) VALUES (%s, %s)",
                (message.from_user.id, message.from_user.username),
            )
            await db.execute(
                f"CREATE TABLE {message.from_user.username} (id INT AUTO_INCREMENT PRIMARY KEY, stuff_link VARCHAR(2048))"
            )

            await bot.send_message(
                message.from_user.id,
                f"Привет, {message.from_user.username}! Ваш вишлист создан.",
            )
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "new_user_registration",
                "New user registered",
            )
        else:
            await bot.send_message(
                message.from_user.id,
                f"Привет, {message.from_user.username}! Что хочешь сделать ?",
            )
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "returning_user_login",
                "Existing user started bot",
            )

        await set_default_keyboard(message.from_user.id)

    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(message.from_user.id,
                  f"Error in start_handler: {e}", error_traceback)
        await bot.send_message(
            message.from_user.id,
            "Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже или обратитесь к администратору.",
        )


@dp.message(StateFilter(States.already_started), Command(commands=["добавить"]))
async def add_item_handler(message: Message, state: FSMContext):
    try:
        await state.set_state(States.adding_item)
        await bot.send_message(
            message.from_user.id,
            "Отправьте сюда ссылку на товар без лишних символов или введите 0 для выхода:",
        )
        log_user_action(
            message.from_user.id,
            message.from_user.username,
            "add_item_started",
            "User initiated adding item",
        )
    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(
            message.from_user.id, f"Error in add_item_handler: {e}", error_traceback
        )
        await bot.send_message(
            message.from_user.id,
            "Произошла ошибка при попытке добавить товар. Пожалуйста, попробуйте позже.",
        )
        await state.set_state(States.already_started)
        await set_default_keyboard(message.from_user.id)


@dp.message(StateFilter(States.adding_item))
async def adding_item(message: Message, state: FSMContext):
    try:
        item_link = message.text

        if item_link == "0":
            await state.set_state(States.already_started)
            await set_default_keyboard(message.from_user.id)
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "add_item_cancelled",
                "User cancelled adding item",
            )
            return

        goods = [
            i[0]
            for i in await db.fetch_all(
                f"SELECT stuff_link FROM {message.from_user.username}"
            )
        ]

        if await check_link_liquidity(item_link):
            if item_link in goods:
                await bot.send_message(
                    message.from_user.id,
                    "Ошибка: ссылка уже есть в вашем списке. Попробуйте другую",
                )
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "add_item_duplicate",
                    f"User tried to add duplicate link: {item_link}",
                )
                return

            await db.execute(
                f"INSERT INTO {message.from_user.username} (stuff_link) VALUES (%s)",
                (item_link,),
            )
            await bot.send_message(
                message.from_user.id, f"Товар добавлен в ваш список."
            )
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "add_item_success",
                f"Added item: {item_link}",
            )

            await state.set_state(States.already_started)
            await set_default_keyboard(message.from_user.id)
        else:
            await bot.send_message(
                message.from_user.id,
                "Ошибка: ссылка не найдена или недоступна. Пожалуйста, убедитесь, что ссылка начинается с 'https://' и попробуйте снова.",
            )
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "add_item_invalid_link",
                f"User tried to add invalid link: {item_link}",
            )

    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(message.from_user.id,
                  f"Error in adding_item: {e}", error_traceback)
        await bot.send_message(
            message.from_user.id,
            "Произошла ошибка при добавлении товара. Пожалуйста, проверьте формат ссылки и попробуйте снова.",
        )
        await state.set_state(States.already_started)
        await set_default_keyboard(message.from_user.id)


@dp.callback_query(F.data.startswith("del_"), StateFilter(States.deleting_item))
async def delete_item(callback_query: CallbackQuery, state: FSMContext):
    try:
        # Получаем индекс товара из callback_data
        item_index = int(callback_query.data.replace("del_", ""))

        # Получаем данные пользователя
        username = callback_query.from_user.username

        wishes = [
            i for i in await db.fetch_all(f"SELECT stuff_link, id FROM {username}")
        ]

        # Удаляем товар по индексу
        if item_index in [i[1] for i in wishes]:
            deleted_item = list(
                filter(lambda x: x[1] == item_index, wishes))[0][0]
            await db.execute(
                f"DELETE FROM {username} WHERE stuff_link = %s", (
                    deleted_item,)
            )
            await db.execute("DELETE FROM want_to_present WHERE host_list = %s AND gift = %s", (username, item_index))

            await callback_query.answer("Товар удален")
            await callback_query.message.delete()
            log_user_action(
                callback_query.from_user.id,
                username,
                "delete_item_success",
                f"Deleted item: {deleted_item}",
            )
        else:
            await callback_query.answer("Товар не найден")
            log_user_action(
                callback_query.from_user.id,
                username,
                "delete_item_not_found",
                f"Item index out of range: {item_index}",
            )

    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(
            callback_query.from_user.id,
            f"Error while deleting item: {e}",
            error_traceback,
        )
        await callback_query.answer("Произошла ошибка при удалении")
        await bot.send_message(
            callback_query.from_user.id,
            "Не удалось удалить товар. Пожалуйста, попробуйте позже.",
        )


@dp.callback_query(F.data == "stop_deleting", StateFilter(States.deleting_item))
async def stop_deleting(callback_query: CallbackQuery, state: FSMContext):
    try:
        await callback_query.answer()
        await callback_query.message.delete()
        await bot.send_message(
            callback_query.from_user.id, "Удаление товаров остановлено."
        )
        await state.set_state(States.already_started)
        await set_default_keyboard(callback_query.from_user.id)
        log_user_action(
            callback_query.from_user.id,
            callback_query.from_user.username,
            "delete_item_stopped",
            "User finished deleting items",
        )
    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(
            callback_query.from_user.id, f"Error in stop_deleting: {e}", error_traceback
        )
        await bot.send_message(
            callback_query.from_user.id,
            "Произошла ошибка. Пожалуйста, попробуйте позже.",
        )
        await state.set_state(States.already_started)
        await set_default_keyboard(callback_query.from_user.id)


@dp.message(StateFilter(States.already_started), Command(commands=["удалить"]))
async def deleting_item_handler(message: Message, state: FSMContext):
    try:
        await state.set_state(States.deleting_item)
        log_user_action(
            message.from_user.id,
            message.from_user.username,
            "delete_item_started",
            "User initiated deleting items",
        )

        wishes = [
            i
            for i in await db.fetch_all(
                f"SELECT stuff_link, id FROM {message.from_user.username}"
            )
        ]

        if not wishes:
            await bot.send_message(message.from_user.id, "Ваш вишлист пуст.")
            await state.set_state(States.already_started)
            await set_default_keyboard(message.from_user.id)
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "delete_item_empty_list",
                "User tried to delete from empty wishlist",
            )
            return

        # Отправляем каждый товар с кнопкой удаления
        for item, index in wishes:
            builder = InlineKeyboardBuilder()
            builder.add(
                types.InlineKeyboardButton(
                    text="Удалить", callback_data=f"del_{index}")
            )
            await bot.send_message(
                message.from_user.id, item, reply_markup=builder.as_markup()
            )

        builder = InlineKeyboardBuilder()
        builder.add(
            types.InlineKeyboardButton(
                text="Закончить", callback_data="stop_deleting")
        )
        await bot.send_message(
            message.from_user.id,
            "Для завершения нажмите:",
            reply_markup=builder.as_markup(),
        )

    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(
            message.from_user.id,
            f"Error in deleting_item_handler: {e}",
            error_traceback,
        )
        await bot.send_message(
            message.from_user.id,
            "Произошла ошибка при загрузке списка товаров. Пожалуйста, попробуйте позже.",
        )
        await state.set_state(States.already_started)
        await set_default_keyboard(message.from_user.id)


@dp.message(StateFilter(States.already_started), Command(commands=["мой_вишлист"]))
async def my_wishlist_handler(message: Message):
    try:
        wishlist = [
            i
            for i in await db.fetch_all(f"SELECT id, stuff_link FROM {message.from_user.username}")
        ]

        if not wishlist:
            await bot.send_message(message.from_user.id, "Ваш вишлист пуст.")
            await set_default_keyboard(message.from_user.id)
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "view_empty_wishlist",
                "User viewed empty wishlist",
            )
            return

        await bot.send_message(message.from_user.id, "Ваш вишлист:")
        for id_, link in wishlist:
            await bot.send_message(message.from_user.id, link)

        log_user_action(
            message.from_user.id,
            message.from_user.username,
            "view_wishlist",
            f"User viewed wishlist with {len(wishlist)} items",
        )

    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(
            message.from_user.id, f"Error in my_wishlist_handler: {e}", error_traceback
        )
        await bot.send_message(
            message.from_user.id,
            "Произошла ошибка при загрузке вишлиста. Пожалуйста, попробуйте позже.",
        )
        await set_default_keyboard(message.from_user.id)


@dp.message(StateFilter(States.already_started), Command(commands=["друзья"]))
async def cmd_friends(message: Message):
    try:
        # Отправляем первую страницу
        await show_friends_page(message, user_id=message.from_user.id, page=0)
        log_user_action(
            message.from_user.id,
            message.from_user.username,
            "view_friends_list",
            "User viewed friends list",
        )
    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(message.from_user.id,
                  f"Error in cmd_friends: {e}", error_traceback)
        await bot.send_message(
            message.from_user.id,
            "Произошла ошибка при загрузке списка друзей. Пожалуйста, попробуйте позже.",
        )
        await set_default_keyboard(message.from_user.id)


async def show_friends_page(message: types.Message, user_id: int, page: int):
    try:
        friends = [
            i[0] if i[1] == user_id else i[1]
            for i in await db.fetch_all(
                "SELECT user_1, user_2 FROM friends_list WHERE (user_1 = %s OR user_2 = %s) AND status = 'accepted' LIMIT %s OFFSET %s",
                (user_id, user_id, ITEMS_PER_PAGE, page * ITEMS_PER_PAGE),
            )
        ]

        # Получаем общее количество друзей
        total_friends = (
            await db.fetch_one(
                "SELECT COUNT(*) FROM friends_list WHERE (user_1 = %s OR user_2 = %s) AND status = 'accepted'",
                (user_id, user_id),
            )
        )[0]

        if not friends:
            if page == 0:
                await message.answer(
                    "У вас пока нет друзей. Добавьте друга, используя команду /добавить_друга"
                )
                log_user_action(
                    user_id,
                    (
                        await db.fetch_one(
                            "SELECT username FROM users WHERE id = %s", (
                                user_id,)
                        )
                    )[0],
                    "view_empty_friends_list",
                    "User viewed empty friends list",
                )
                return
            else:
                # Если на этой странице нет друзей, но они есть на предыдущих страницах
                await message.answer("На этой странице больше нет друзей.")
                return

        # Создаем клавиатуру с кнопками для друзей
        builder = InlineKeyboardBuilder()
        for friend in friends:
            friend_name = (
                await db.fetch_one(
                    "SELECT username FROM users WHERE id = %s", (friend,)
                )
            )[0]
            builder.add(
                types.InlineKeyboardButton(
                    text=friend_name, callback_data=f"friend_{friend}"
                )
            )

        # Добавляем кнопки для навигации (расположим в отдельном ряду)
        row = []
        if page > 0:
            row.append(
                types.InlineKeyboardButton(
                    text=emojize(":left_arrow:"), callback_data=f"page_{page - 1}"
                )
            )
        if (page + 1) * ITEMS_PER_PAGE < total_friends:
            row.append(
                types.InlineKeyboardButton(
                    text=emojize(":right_arrow:"), callback_data=f"page_{page + 1}"
                )
            )
        if row:
            builder.row(*row)

        # Редактируем сообщение, если оно уже существует
        if hasattr(message, "message_id") and message.message_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text=f"Страница {page + 1}. Выберите друга:",
                    reply_markup=builder.as_markup(),
                )
            except Exception as e:
                await message.answer(
                    f"Страница {page + 1}. Выберите друга:",
                    reply_markup=builder.as_markup(),
                )
        else:
            # Если сообщение новое (например, первая страница)
            await message.answer(
                f"Страница {page + 1}. Выберите друга:",
                reply_markup=builder.as_markup(),
            )
        log_user_action(
            user_id,
            (
                await db.fetch_one(
                    "SELECT username FROM users WHERE id = %s", (user_id,)
                )
            )[0],
            "view_friends_page",
            f"User viewed friends page {page + 1} with {len(friends)} friends",
        )

    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(user_id, f"Error in show_friends_page: {e}", error_traceback)
        await message.answer(
            "Произошла ошибка при загрузке списка друзей. Пожалуйста, попробуйте позже."
        )


@dp.callback_query(F.data.startswith("friend_"))
async def process_friend_selection(callback_query: types.CallbackQuery):
    try:
        friend_id = int(callback_query.data.split("_")[1])
        friend_name = (
            await db.fetch_one("SELECT username FROM users WHERE id = %s", (friend_id,))
        )[0]

        wishes = [i for i in await db.fetch_all(f"SELECT id, stuff_link FROM {friend_name}")]

        if not wishes:
            await bot.send_message(
                callback_query.from_user.id, f"Вишлист @{friend_name} пуст."
            )
            await set_default_keyboard(callback_query.from_user.id)
            log_user_action(
                callback_query.from_user.id,
                callback_query.from_user.username,
                "view_friend_empty_wishlist",
                f"User viewed empty wishlist of friend @{friend_name}",
            )
            await callback_query.answer()
            return

        await bot.send_message(callback_query.from_user.id, f"Вишлист @{friend_name}:")
        for id_, link in wishes:
            builder = InlineKeyboardBuilder()
            someone_want = (await db.fetch_one("SELECT gifter FROM want_to_present WHERE host_list = %s AND gift = %s", (friend_name, id_)))
            if someone_want:
                someone_want = someone_want[0]
                if someone_want == callback_query.from_user.username:
                    builder.add(
                        types.InlineKeyboardButton(
                            text="Вы уже дарите это", callback_data=f"want^{friend_name}^{id_}^del"
                        )
                    )
                elif someone_want != callback_query.from_user.username:
                    builder.add(
                        types.InlineKeyboardButton(
                            text=f"Это уже дарит @{someone_want}", callback_data="none"
                        )
                    )
            else:
                builder.add(
                    types.InlineKeyboardButton(
                        text="Хочу подарить", callback_data=f"want^{friend_name}^{id_}^add"
                    )
                )

            await bot.send_message(callback_query.from_user.id, link, reply_markup=builder.as_markup())

        log_user_action(
            callback_query.from_user.id,
            callback_query.from_user.username,
            "view_friend_wishlist",
            f"User viewed wishlist of friend @{friend_name} with {len(wishes)} items",
        )
        # Подтверждаем обработку callback
        await callback_query.answer()

    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(
            callback_query.from_user.id,
            f"Error in process_friend_selection: {e}",
            error_traceback,
        )
        await callback_query.answer("Произошла ошибка")
        await bot.send_message(
            callback_query.from_user.id,
            "Произошла ошибка при загрузке вишлиста друга. Пожалуйста, попробуйте позже.",
        )


@dp.callback_query(F.data.startswith("want^"))
async def want_to_gift(callback_query: CallbackQuery):
    try:
        friend_name, gift_id, action = callback_query.data.split("^")[1::]
        skip = False
        new_markup = InlineKeyboardBuilder()
        someone_want = (await db.fetch_one("SELECT gifter FROM want_to_present WHERE host_list = %s AND gift = %s", (friend_name, gift_id)))
        if someone_want:
            someone_want = someone_want[0]
            if someone_want != callback_query.from_user.username:
                new_markup.add(
                    types.InlineKeyboardButton(
                        text=f"Это уже дарит @{someone_want}", callback_data="none"
                    )
                )
                skip = True
        if not skip:
            if action == "del":
                await db.execute(
                    "DELETE FROM want_to_present WHERE host_list = %s AND gift = %s AND gifter = %s",
                    (friend_name, gift_id, callback_query.from_user.username),
                )
                new_markup.add(types.InlineKeyboardButton(
                    text="Хочу подарить", callback_data=f"want^{friend_name}^{gift_id}^add"))
            elif action == "add":
                await db.execute(
                    "INSERT INTO want_to_present (host_list, gift, gifter) VALUES (%s, %s, %s)",
                    (friend_name, gift_id, callback_query.from_user.username),
                )
                new_markup.add(types.InlineKeyboardButton(
                    text="Вы уже дарите это", callback_data=f"want^{friend_name}^{gift_id}^del"))
        await callback_query.message.edit_reply_markup(reply_markup=new_markup.as_markup())
        await callback_query.answer()
    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(
            callback_query.from_user.id,
            f"Error in want_to_gift: {e}",
            error_traceback,
        )
        await callback_query.answer("Произошла ошибка")
        await bot.send_message(
            callback_query.from_user.id,
            "Произошла ошибка при изменении статуса дарения. Пожалуйста, попробуйте позже.",
        )


@dp.callback_query(F.data.startswith("none"))
async def none_handler(callback_query: CallbackQuery):
    await callback_query.answer()


@dp.callback_query(F.data.startswith("page_"))
async def process_page_selection(callback_query: types.CallbackQuery):
    try:
        page = int(callback_query.data.split("_")[1])
        await show_friends_page(
            callback_query.message, user_id=callback_query.from_user.id, page=page
        )
        await callback_query.answer()
        log_user_action(
            callback_query.from_user.id,
            callback_query.from_user.username,
            "navigate_friends_page",
            f"User navigated to friends page {page + 1}",
        )

    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(
            callback_query.from_user.id,
            f"Error in process_page_selection: {e}",
            error_traceback,
        )
        await callback_query.answer("Произошла ошибка при навигации")
        await bot.send_message(
            callback_query.from_user.id,
            "Произошла ошибка при переходе на другую страницу. Пожалуйста, попробуйте позже.",
        )


@dp.message(StateFilter(States.already_started), F.user_shared)
async def adding_friend(message: Message, state: FSMContext):
    try:
        friend_id = message.user_shared.user_id
        users_list = [i[0] for i in await db.fetch_all("SELECT id FROM users")]

        if friend_id not in users_list:
            await bot.send_message(
                message.chat.id, f"Пользователь не зарегистрирован в данном боте."
            )
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "invalid_input",
                f"tried to add non-existent user: {friend_id}",
            )
            return

        if friend_id == message.from_user.id:
            await bot.send_message(
                message.chat.id, "Вы не можете добавить себя в друзья."
            )
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "invalid_input",
                "tried to add themselves as friend",
            )
            return

        user1 = message.from_user.id
        user2 = friend_id
        username = (await bot.get_chat(friend_id)).username
        # Проверяем историю запросов дружбы
        old_request = await db.fetch_one(
            "SELECT status, time FROM friends_list WHERE user_1 IN (%s, %s) AND user_2 IN (%s, %s)",
            (user1, user2, user1, user2),
        )

        if old_request:
            if old_request[0] == "accepted":
                await bot.send_message(
                    message.chat.id,
                    f"Вы уже друзья с @{username}. Попробуйте другой юзернейм",
                )
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "invalid_input",
                    f"tried to add existing friend: @{username}",
                )
                return

            if old_request[0] in ("waiting", "rejected"):
                old_time = old_request[1]
                time_since_request = (
                    datetime.now() - old_time).total_seconds() // 60

                if time_since_request < 5:
                    await bot.send_message(
                        message.chat.id,
                        f"Предыдущий запрос @{username} был отправлен менее 5 минут  назад. Попробуйте позже.",
                    )
                    log_user_action(
                        message.from_user.id,
                        message.from_user.username,
                        "invalid_input",
                        f"tried to send friend request too soon to: @{username}",
                    )
                    return
                else:
                    await db.execute(
                        "DELETE FROM friends_list WHERE user_1 IN (%s, %s) AND user_2 IN (%s, %s)",
                        (user1, user2, user1, user2),
                    )
                    main_logger.info(
                        f"Deleted old friend request between {user1} and {user2}"
                    )

        # Создаем новый запрос дружбы
        await db.execute(
            "INSERT INTO friends_list VALUES(%s, %s, 'waiting', %s)",
            (user1, user2, datetime.now()),
        )

        await bot.send_message(
            message.chat.id, f"Запрос дружбы отправлен @{username}"
        )
        await state.set_state(States.already_started)
        await set_default_keyboard(message.chat.id)

        # Отправляем уведомление пользователю
        builder = InlineKeyboardBuilder()
        builder.add(
            types.InlineKeyboardButton(
                text="Принять",
                callback_data=f"accept_friend^{user1}",
            )
        )
        builder.add(
            types.InlineKeyboardButton(
                text="Отклонить",
                callback_data=f"reject_friend^{user1}",
            )
        )

        await bot.send_message(
            friend_id,
            f"@{message.from_user.username} хочет добавить вас в друзья. Принять заявку?",
            reply_markup=builder.as_markup(),
        )

        log_user_action(
            message.from_user.id,
            message.from_user.username,
            "send_request" f"sent friend request to: @{username}",
        )

    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(message.from_user.id,
                  f"Error in adding_friend: {e}", error_traceback)
        await bot.send_message(
            message.chat.id, "Произошла ошибка при добавлении друга. Попробуйте позже."
        )

        await state.set_state(States.already_started)
        await set_default_keyboard(message.chat.id)


@dp.callback_query(
    F.data.startswith("accept_friend"), StateFilter(States.already_started)
)
async def accept_friend(callback_query: CallbackQuery):
    try:
        friend_id = callback_query.data.split("^")[1]
        user_id = callback_query.from_user.id
        friend_name = (
            await db.fetch_one("SELECT username FROM users WHERE id = %s", (friend_id,))
        )[0]

        await callback_query.answer()

        # Обновление статуса дружбы
        await db.execute(
            "UPDATE friends_list SET status = 'accepted' WHERE user_1 IN (%s, %s) AND user_2 IN (%s, %s)",
            (user_id, friend_id, user_id, friend_id),
        )

        # Отправка уведомлений
        await bot.send_message(
            int(friend_id),
            f"@{callback_query.from_user.username} принял ваш запрос дружбы.",
        )
        await bot.send_message(int(user_id), f"Вы добавили @{friend_name} в друзья.")

        log_user_action(
            user_id,
            callback_query.from_user.username,
            "accept friend" f"accepted friend request from @{friend_name}",
        )

    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(user_id, f"Error in accept_friend: {e}", error_traceback)
        await bot.send_message(
            callback_query.from_user.id,
            "Произошла ошибка при принятии запроса дружбы. Попробуйте позже.",
        )


@dp.callback_query(
    F.data.startswith("reject_friend"), StateFilter(States.already_started)
)
async def reject_friend(callback_query: CallbackQuery):
    try:
        friend_id = callback_query.data.split("^")[1]
        user_id = callback_query.from_user.id
        friend_name = (
            await db.fetch_one("SELECT username FROM users WHERE id = %s", (friend_id,))
        )[0]

        await callback_query.answer()

        # Обновление статуса дружбы
        await db.execute(
            "UPDATE friends_list SET status = 'rejected' WHERE user_1 IN (%s, %s) AND user_2 IN (%s, %s)",
            (user_id, friend_id, user_id, friend_id),
        )

        # Отправка уведомлений
        await bot.send_message(
            int(friend_id),
            f"@{callback_query.from_user.username} отклонил ваш запрос дружбы.",
        )
        await bot.send_message(int(user_id), "Запрос отклонен")

        log_user_action(
            user_id,
            callback_query.from_user.username,
            "rejection",
            f"rejected friend request from @{friend_name}",
        )

    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(
            callback_query.from_user.id, f"Error in reject_friend: {e}", error_traceback
        )
        await bot.send__message(
            callback_query.from_user.id,
            "Произошла ошибка при отклонении запроса дружбы. Попробуйте позже.",
        )


@dp.message(default_state)
async def refresh_handler(message: Message):
    await bot.send_message(message.from_user.id, "Сервер был перезагружен. Нажмите /start")


async def on_shutdown():
    main_logger.info("Starting bot shutdown...")
    try:
        await bot.session.close()
        main_logger.info("Bot session was closed successfully")
        await db.close()
    except Exception as e:
        main_logger.info(f"Error with bot session closig: {e}")

    main_logger.info("Shutdown completed successfully")


async def main():
    main_logger.info("Bot starting...")

    try:
        main_logger.info("Polling starting...")
        await dp.start_polling(bot)
    except Exception as e:
        main_logger.error(f"Critical error: {e}")
        raise
    finally:
        await on_shutdown()
        main_logger.info("Bot is stopped")


if __name__ == "__main__":
    dp.message.middleware(BanMiddleware())
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        main_logger.info("Exit is caught...")
    except Exception as e:
        main_logger.error(f"Uncaught error: {e}")
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
            main_logger.error(f"Error with loop closing: {e}")
        main_logger.info("Program is fiished")
