from typing import Optional, List
import aiomysql
from contextlib import asynccontextmanager
import logging
import config


class DatabaseManager:
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        min_connections: int = 10,
        max_connections: int = 20
    ):
        """
        Инициализация менеджера базы данных

        :param host: хост базы данных
        :param user: пользователь
        :param password: пароль
        :param database: название базы данных
        :param min_connections: минимальное количество соединений в пуле
        :param max_connections: максимальное количество соединений в пуле
        """
        handler = logging.FileHandler(config.LOG_DIR / 'database.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.host = host
        self.port = 3306
        self.user = user
        self.password = password
        self.database = database
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool: Optional[aiomysql.Pool] = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    async def initialize(self) -> None:
        """Создание пула соединений"""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.database,
                minsize=self.min_connections,
                maxsize=self.max_connections,
                autocommit=True,
                pool_recycle=3600  # Переподключение каждый час
            )
            self.logger.info("Database connection pool created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create database pool: {e}")
            raise

    async def close(self) -> None:
        """Закрытие пула соединений"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.logger.info("Database connection pool closed")

    @asynccontextmanager
    async def connection(self):
        """Контекстный менеджер для получения соединения из пула"""
        if not self.pool:
            await self.initialize()

        async with self.pool.acquire() as conn:
            try:
                yield conn
            except Exception as e:
                self.logger.error(f"Database operation failed: {e}")
                raise

    async def execute(self, query: str, params: tuple = None) -> None:
        """
        Выполнение SQL запроса без возврата результатов

        :param query: SQL запрос
        :param params: параметры запроса
        """
        async with self.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                await conn.commit()

    async def fetch_one(self, query: str, params: tuple = None) -> Optional[tuple]:
        """
        Получение одной записи

        :param query: SQL запрос
        :param params: параметры запроса
        :return: результат запроса или None
        """
        async with self.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return await cur.fetchone()

    async def fetch_all(self, query: str, params: tuple = None) -> List[tuple]:
        """
        Получение всех записей

        :param query: SQL запрос
        :param params: параметры запроса
        :return: список результатов
        """
        async with self.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return await cur.fetchall()


# Пример использования:


db = DatabaseManager(
    host=config.MYSQLHOST,
    user=config.MYSQLUSER,
    password=config.MYSQLPASSWORD,
    database=config.MYSQLDB,
    min_connections=10,
    max_connections=20
)
