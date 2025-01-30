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
from pathlib import Path
import logging

# Конфигурация
SCRIPT_DIR = Path(__file__).parent
WISHLISTS_DIR = SCRIPT_DIR / "wishlists"
WISHLISTS_DIR.mkdir(exist_ok=True)

token = "7802068134:AAFrKpQwLbpTOCsurdGw0QfBPVvOd6oR8_g"
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


if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def check_link_liquidity(link):
    try:
        response = requests.head(link)
        if link.startswith("https://"):
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False


async def set_default_keyboard(chat_id):
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="/добавить"))
    builder.row(types.KeyboardButton(text="/удалить"))
    builder.row(types.KeyboardButton(text="/посмотреть"))
    await bot.send_message(chat_id, "Выберите действие:", reply_markup=builder.as_markup(resize_keyboard=True))


@dp.message(StateFilter(default_state, States.already_started), Command(commands=["start"]))
async def start_handler(message: Message, state: FSMContext):
    await state.set_state(States.already_started)
    users_file = SCRIPT_DIR / "users.txt"

    # Создаём файл пользователей, если его нет
    if not users_file.exists():
        users_file.touch()

    with open(users_file) as users:
        users_list = users.read().splitlines()

    if str(message.from_user.id) not in users_list:
        with open(users_file, 'a') as users:
            users.write(f"{message.from_user.id}\n")

        wishlist_path = WISHLISTS_DIR / \
            f"whishlist^{message.from_user.username}^{message.from_user.id}.txt"
        wishlist_path.touch()  # Создаём пустой файл вишлиста

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
    if item_link == "0":
        await state.set_state(States.already_started)
        await set_default_keyboard(message.from_user.id)
        return
    if await check_link_liquidity(item_link):
        wishlist_path = WISHLISTS_DIR / \
            f"whishlist^{message.from_user.username}^{message.from_user.id}.txt"
        with open(wishlist_path, 'a') as wishlist:
            wishlist.write(f"{item_link}\n")
        await bot.send_message(message.from_user.id, f"Товар добавлен в ваш список.")
        await state.set_state(States.already_started)
        await set_default_keyboard(message.from_user.id)
    else:
        await bot.send_message(message.from_user.id, "Ошибка: ссылка не найдена или недоступна. Попробуйте еще раз")


@dp.callback_query(F.data.startswith("del_"), StateFilter(States.deleting_item))
async def delete_item(callback_query: CallbackQuery, state: FSMContext):
    try:
        # Получаем индекс товара из callback_data
        item_index = int(callback_query.data.replace("del_", ""))

        # Получаем данные пользователя
        username = callback_query.from_user.username
        user_id = callback_query.from_user.id
        wishlist_path = WISHLISTS_DIR / f"whishlist^{username}^{user_id}.txt"

        # Читаем список товаров
        with open(wishlist_path, 'r') as wh:
            wishes = wh.read().splitlines()

        # Удаляем товар по индексу
        if 0 <= item_index < len(wishes):
            wishes.pop(item_index)
            # Записываем обновленный список
            with open(wishlist_path, 'w') as wh:
                wh.write('\n'.join(wishes) + '\n')

            await callback_query.answer("Товар удален")
            await callback_query.message.delete()
        else:
            await callback_query.answer("Товар не найден")

    except Exception as e:
        await callback_query.answer("Произошла ошибка при удалении")
        logger.error(f"Ошибка при удалении: {e}")


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
    wishlist_path = WISHLISTS_DIR / \
        f"whishlist^{message.from_user.username}^{message.from_user.id}.txt"

    try:
        with open(wishlist_path) as wh:
            wishes = wh.read().splitlines()

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
        logger.error(f"Ошибка при загрузке вишлиста: {e}")
        await state.set_state(States.already_started)
        await set_default_keyboard(message.from_user.id)


@dp.message(StateFilter(States.already_started), Command(commands=["посмотреть"]))
async def view_wishlists_handler(message: Message, state: FSMContext):
    await state.set_state(States.viewing_wishlists)

    # Получаем список всех файлов вишлистов из правильной директории
    wishlist_files = list(WISHLISTS_DIR.glob("whishlist^*^*.txt"))

    if not wishlist_files:
        await bot.send_message(message.from_user.id, "Пока нет ни одного вишлиста.")
        await state.set_state(States.already_started)
        await set_default_keyboard(message.from_user.id)
        return

    builder = InlineKeyboardBuilder()
    for wishlist_file in wishlist_files:
        try:
            username = wishlist_file.name.split('^')[1]
            user_id = wishlist_file.name.split('^')[2].replace('.txt', '')

            builder.add(types.InlineKeyboardButton(
                text=username,
                callback_data=f"view^{username}^{user_id}"
            ))

        except Exception as e:
            logger.error(f"Ошибка при обработке файла {wishlist_file}: {e}")
            continue

    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(
        text="Назад",
        callback_data="back_to_main"
    ))

    await bot.send_message(
        message.from_user.id,
        "Выберите вишлист для просмотра:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("view"), StateFilter(States.viewing_wishlists))
async def show_wishlist(callback_query: CallbackQuery, state: FSMContext):
    try:
        _, username, user_id = callback_query.data.split('^')
        wishlist_file = WISHLISTS_DIR / f"whishlist^{username}^{user_id}.txt"
        await callback_query.answer()
        await callback_query.message.delete()

        if not wishlist_file.exists():
            await bot.send_message(
                callback_query.from_user.id,
                "Вишлист не найден."
            )
            await state.set_state(States.already_started)
            await set_default_keyboard(callback_query.from_user.id)
            return

        with open(wishlist_file, 'r') as wh:
            wishes = wh.read().splitlines()

        if not wishes:
            await bot.send_message(
                callback_query.from_user.id,
                f"Вишлист пользователя {username} пуст."
            )
        else:
            await bot.send_message(
                callback_query.from_user.id,
                f"Вишлист пользователя {username}:"
            )

            for wish in wishes:
                await bot.send_message(callback_query.from_user.id, wish)

        await state.set_state(States.already_started)
        await set_default_keyboard(callback_query.from_user.id)

    except Exception as e:
        await bot.send_message(
            callback_query.from_user.id,
            "Произошла ошибка при загрузке вишлиста."
        )
        logger.error(f"Ошибка при показе вишлиста: {e}")
        await state.set_state(States.already_started)
        await set_default_keyboard(callback_query.from_user.id)


@dp.callback_query(F.data == "back_to_main", StateFilter(States.viewing_wishlists))
async def back_to_main(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.delete()
    await state.set_state(States.already_started)
    await set_default_keyboard(callback_query.from_user.id)


async def on_shutdown():
    logger.info("Начало завершения работы бота...")
    try:
        await bot.session.close()
        logger.info("Сессия бота закрыта")
    except Exception as e:
        logger.info(f"Ошибка при закрытии сессии бота: {e}")

    logger.info("Shutdown завершен")


async def main():
    logger.info("Запуск бота...")

    try:
        logger.info("Запуск поллинга...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise
    finally:
        await on_shutdown()
        logger.info("Бот остановлен")

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Получено прерывание...")
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}")
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
            logger.error(f"Ошибка при закрытии loop: {e}")
        logger.info("Программа завершена")
