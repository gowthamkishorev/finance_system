"""
Seed script: Creates demo users and sample transactions on first run.
Safe to call multiple times (skips if data already exists).
"""
from datetime import datetime, timedelta, timezone
import random

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.transaction import Transaction, TransactionType, Category
from app.auth import hash_password


DEMO_USERS = [
    {"username": "admin", "email": "admin@fintrack.dev", "password": "admin123", "role": UserRole.admin},
    {"username": "alice", "email": "alice@fintrack.dev", "password": "alice123", "role": UserRole.analyst},
    {"username": "bob", "email": "bob@fintrack.dev", "password": "bob123", "role": UserRole.viewer},
]

INCOME_CATEGORIES = [Category.salary, Category.freelance, Category.investment]
EXPENSE_CATEGORIES = [
    Category.food, Category.transport, Category.housing,
    Category.entertainment, Category.healthcare, Category.utilities, Category.shopping,
]


def _random_transactions(owner_id: int, count: int) -> list[Transaction]:
    transactions = []
    for i in range(count):
        is_income = random.random() < 0.4
        t_type = TransactionType.income if is_income else TransactionType.expense
        category = random.choice(INCOME_CATEGORIES if is_income else EXPENSE_CATEGORIES)
        amount = round(random.uniform(50, 5000 if is_income else 500), 2)
        date = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 180))
        transactions.append(Transaction(
            amount=amount,
            type=t_type,
            category=category,
            date=date,
            notes=f"Sample {t_type.value} #{i + 1}",
            owner_id=owner_id,
        ))
    return transactions


def seed_database():
    db = SessionLocal()
    try:
        # Skip if already seeded
        if db.query(User).first():
            return

        print("Seeding database with demo data...")

        users = []
        for u in DEMO_USERS:
            user = User(
                username=u["username"],
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                role=u["role"],
            )
            db.add(user)
            db.flush()  # Get the ID before committing
            users.append(user)

        # Add transactions for admin and alice
        for user in users[:2]:
            for t in _random_transactions(user.id, 30):
                db.add(t)

        db.commit()
        print(f"Seeded {len(users)} users with sample transactions.")
        print("\nDemo credentials:")
        for u in DEMO_USERS:
            print(f"  {u['role'].value:8s}  username={u['username']!r}  password={u['password']!r}")

    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    from app.database import engine, Base
    Base.metadata.create_all(bind=engine)
    seed_database()
