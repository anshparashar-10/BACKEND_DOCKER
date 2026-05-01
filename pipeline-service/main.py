from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db, init_db
from models.customer import Customer
from services.ingestion import run_ingestion

app = FastAPI(
    title="Customer Pipeline Service",
    description="Ingests customer data from Flask mock server into PostgreSQL",
    version="1.0.0"
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "pipeline-service"}


@app.post("/api/ingest")
def ingest_customers(db: Session = Depends(get_db)):
    """
    Fetch all customers from the Flask mock server (handling pagination)
    and upsert them into PostgreSQL.
    """
    try:
        result = run_ingestion(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/api/customers")
def list_customers(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Return paginated list of customers from PostgreSQL."""
    total = db.query(Customer).count()
    offset = (page - 1) * limit
    customers = db.query(Customer).offset(offset).limit(limit).all()

    return {
        "data": [c.to_dict() for c in customers],
        "total": total,
        "page": page,
        "limit": limit
    }


@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Return a single customer by ID or 404 if not found."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")
    return {"data": customer.to_dict()}
