
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import sessionmaker
from .setting import get_settings  


# 1. Load system or .env variables via your settings utility
settings = get_settings()

user = settings.DB_USERNAME
password = settings.DB_PASSWORD
dsn = settings.DB_DSN

# 2. Initialize the Oracle connection engine using python-oracledb thick/thin driver
engine = create_engine(f"oracle+oracledb://{user}:{password}@{dsn}", enable_offset_fetch=False)  # Set echo=True for SQL logging

# 3. Create the database session factory layout
Session = sessionmaker(bind=engine)

# 4. Modern SQLAlchemy 2.0 Declarative Base Class (Fixes ORA-01400 / legacy issues)
class Base(DeclarativeBase):
    pass

# 5. Dependency generator function to open/close session handles safely in FastAPI
def init_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()