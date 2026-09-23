from logging.config import fileConfig

from sqlalchemy import engine_from_config, false
from sqlalchemy import pool
from src.utils.setting import Settings  
from src.User.model import UserModel  # Import your UserModel here
from src.utils.db import Base  # Import your Base here
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option(
    "sqlalchemy.url", 
    f"oracle+oracledb://{Settings().DB_USERNAME}:{Settings().DB_PASSWORD}@{Settings().DB_DSN}?sid={Settings().DB_DSN.split('/')[-1]}"
)

target_metadata = Base.metadata  # Use the metadata from your Base class


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
   
    def include_object(object, name, type_, reflected, compare_to):
        if type_ == "table":
            return name.upper() in ["USER_TABLE", "ALEMBIC_HISTORY", "friend_requests"]
        return True
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_schemas=False,  # Correctly placed to fix Oracle table lookups
            version_table="alembic_history",
            include_object=include_object
            
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
