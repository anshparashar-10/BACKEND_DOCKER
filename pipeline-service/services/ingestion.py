import httpx
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models.customer import Customer

FLASK_BASE_URL = "http://mock-server:5000"
BATCH_SIZE = 10


def fetch_all_customers() -> list[dict]:
    """Fetch all customers from Flask mock server, handling pagination."""
    all_customers = []
    page = 1

    with httpx.Client(timeout=30.0) as client:
        while True:
            response = client.get(
                f"{FLASK_BASE_URL}/api/customers",
                params={"page": page, "limit": BATCH_SIZE}
            )
            response.raise_for_status()
            payload = response.json()

            data = payload.get("data", [])
            all_customers.extend(data)

            total = payload.get("total", 0)
            if len(all_customers) >= total or not data:
                break

            page += 1

    return all_customers


def parse_customer(raw: dict) -> dict:
    """Parse and coerce raw dict into DB-ready types."""
    dob = raw.get("date_of_birth")
    if dob:
        try:
            dob = date.fromisoformat(dob)
        except ValueError:
            dob = None

    created_at = raw.get("created_at")
    if created_at:
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            created_at = None

    balance = raw.get("account_balance")
    if balance is not None:
        balance = Decimal(str(balance))

    return {
        "customer_id": raw["customer_id"],
        "first_name": raw["first_name"],
        "last_name": raw["last_name"],
        "email": raw["email"],
        "phone": raw.get("phone"),
        "address": raw.get("address"),
        "date_of_birth": dob,
        "account_balance": balance,
        "created_at": created_at,
    }


def upsert_customers(db: Session, customers: list[dict]) -> int:
    """Upsert customers into PostgreSQL. Returns count of records processed."""
    if not customers:
        return 0

    parsed = [parse_customer(c) for c in customers]

    stmt = pg_insert(Customer).values(parsed)
    stmt = stmt.on_conflict_do_update(
        index_elements=["customer_id"],
        set_={
            "first_name": stmt.excluded.first_name,
            "last_name": stmt.excluded.last_name,
            "email": stmt.excluded.email,
            "phone": stmt.excluded.phone,
            "address": stmt.excluded.address,
            "date_of_birth": stmt.excluded.date_of_birth,
            "account_balance": stmt.excluded.account_balance,
            "created_at": stmt.excluded.created_at,
        }
    )
    db.execute(stmt)
    db.commit()

    return len(parsed)


def run_ingestion(db: Session) -> dict:
    """Full ingestion pipeline: fetch → parse → upsert."""
    customers = fetch_all_customers()
    count = upsert_customers(db, customers)
    return {"status": "success", "records_processed": count}
