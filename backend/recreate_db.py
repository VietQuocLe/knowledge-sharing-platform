from app.core.database import SessionLocal, engine
from app.models import Base
from app.services.startup_service import initialize_system

def main():
    print("Dropping all existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables with new schema (payment_orders, user.tier, user.pro_expires_at)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        initialize_system(db)
        print("Default admin created/verified successfully!")
    finally:
        db.close()

    print(">>> Database recreated and initialized successfully!")

if __name__ == "__main__":
    main()
