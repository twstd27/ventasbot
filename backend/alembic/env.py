import asyncio
from logging.config import fileConfig

from sqlalchemy.engine import Connection

from alembic import context
from app import models  # noqa: F401  (registra todos los modelos)

# Importar el engine async ya configurado (incluye SSL para Supabase)
# y todos los modelos para que Base.metadata conozca todas las tablas.
from app.database import Base, engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    raise RuntimeError("Modo offline no soportado; se requiere conexión a la base.")
else:
    run_migrations_online()
