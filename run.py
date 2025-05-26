import uvicorn
from app.core.database import SessionLocal, create_tables
from app.db.init_db import init_db


def main():
    # Create all database tables first
    create_tables()

    # Initialize database with test data
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()

    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5001,  # Using port 5001 instead of 5000 to avoid conflicts
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
