from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite database URL
DATABASE_URL = "sqlite:///./transaction_anomaly.db"

# Create the database engine
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # Required for SQLite
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all database models
Base = declarative_base()


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
