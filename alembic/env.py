from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app import models  # noqa: F401  - register models with Base.metadata
from app.config import settings
from app.database import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.databaseUrl)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def runMigrationsOffline() -> None:
    context.configure(
        url=settings.databaseUrl,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def runMigrationsOnline() -> None:
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = settings.databaseUrl
    connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    runMigrationsOffline()
else:
    runMigrationsOnline()
