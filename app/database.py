from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chat.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

# Define Tables using Core (so we can use them in migrations or queries later easily)
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String, unique=True),
    Column("hashed_password", String),
    Column("created_at", String),
)

conversations = Table(
    "conversations",
    metadata,
    Column("id", String, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("created_at", String),
)

messages = Table(
    "messages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("conversation_id", String, ForeignKey("conversations.id")),
    Column("role", String),
    Column("content", Text),
    Column("timestamp", String),
)

def init_db():
    metadata.create_all(bind=engine)

def get_db():
    """Yields a SQLAlchemy Database Connection (or Session)"""
    try:
        # Use simple connection for Core-like usage if preferable, but Session is standard
        db = SessionLocal()
        yield db
    finally:
        db.close()
