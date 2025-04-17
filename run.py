import uvicorn
from app.core.database import SessionLocal
from app.db.init_db import init_db


def main():
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
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()