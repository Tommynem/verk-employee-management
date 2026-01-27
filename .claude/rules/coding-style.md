# Verk Bookkeeping Coding Style

This rule defines the coding conventions for Verk Bookkeeping development using FastAPI, Jinja2, HTMX, and Tailwind CSS.

## Core Principles

- **Clarity over cleverness**: Code should be self-explanatory
- **Consistency over preference**: Follow existing patterns
- **Explicit over implicit**: Clear intentions and behavior
- **VaWW compatibility**: Match VaWW patterns for future addon integration

---

## Python (Backend)

### Formatting

- **Line length**: 120 characters maximum
- **Indentation**: 4 spaces
- **Tools**: Black formatter, isort for imports
- **Automation**: `make format` applies Black + isort

### Imports

```python
# Order: stdlib, third-party, local (with blank lines between)
import os
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from source.api.dependencies import get_db
from source.database.models import Invoice, CashEntry
```

**Import Rules**:
- **Always use absolute imports** from `source/`
- **No wildcard imports** (`from module import *`)
- **Sort alphabetically** within groups
- **Separate groups** with blank lines

### Naming Conventions

```python
# Variables/Functions: snake_case
invoice_total = calculate_total(items)
def get_invoice_by_id(invoice_id: int) -> Invoice:

# Classes: PascalCase
class InvoiceCreate(BaseModel):

# Constants: UPPER_SNAKE_CASE
MAX_INVOICE_AMOUNT = Decimal("999999.99")

# Protected/Private: underscore prefix
self._cached_total = None
```

### Type Annotations

All functions must have type hints for parameters and return values.

```python
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db)
) -> InvoiceResponse:
    """Create a new invoice."""
    ...

def get_invoice(id: int) -> Optional[Invoice]:
    """Get invoice by ID, returns None if not found."""
    ...
```

---

## FastAPI Routes

### Route Patterns

```python
router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.get("")
async def list_invoices(request: Request, db: Session = Depends(get_db)):
    """List all invoices (browser view)."""
    ...

@router.get("/new")
async def new_invoice_form(request: Request):
    """Show new invoice form."""
    ...

@router.post("", status_code=201)
async def create_invoice(
    request: Request,
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db)
):
    """Create new invoice, return detail partial."""
    ...

@router.get("/{invoice_id}")
async def get_invoice(request: Request, invoice_id: int, db: Session = Depends(get_db)):
    """Get invoice detail view."""
    ...

@router.patch("/{invoice_id}")
async def update_invoice(
    request: Request,
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db)
):
    """Update invoice, return detail partial."""
    ...

@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Delete invoice."""
    ...
```

### HTMX Response Pattern

```python
from fastapi.responses import HTMLResponse
from source.api.context import render_template

@router.post("", status_code=201)
async def create_invoice(request: Request, invoice_data: InvoiceCreate, db: Session = Depends(get_db)):
    invoice = Invoice(**invoice_data.model_dump())
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    html = render_template(request, "partials/_detail_invoice.html", invoice=invoice)
    response = HTMLResponse(content=html, status_code=201)
    response.headers["HX-Trigger"] = "invoiceCreated"
    return response
```

---

## Pydantic Schemas

### Schema Pattern (Match VaWW)

```python
from decimal import Decimal
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict

class InvoiceUpdate(BaseModel):
    """Base with all fields and validators."""
    counterparty_name: str = Field(..., min_length=1)
    gross_amount: Decimal = Field(ge=Decimal("0.01"))
    category: Optional[str] = None
    notes: Optional[str] = None

class InvoiceCreate(InvoiceUpdate):
    """Inherits all from Update, adds required fields."""
    direction: Literal["incoming", "outgoing"]
    invoice_date: date

class InvoiceResponse(InvoiceUpdate):
    """Adds database fields for responses."""
    id: int
    direction: str
    invoice_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

---

## SQLAlchemy Models

### Model Definition

```python
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, func

class Invoice(Base):
    __tablename__ = "invoices"

    # Primary key first
    id = Column(Integer, primary_key=True)

    # Required fields
    direction = Column(String(20), nullable=False)  # 'incoming' or 'outgoing'
    counterparty_name = Column(String(255), nullable=False)
    gross_amount = Column(Numeric(10, 2), nullable=False)
    invoice_date = Column(Date, nullable=False)

    # Optional fields
    category = Column(String(100), nullable=True)
    notes = Column(String, nullable=True)

    # Timestamps last
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

---

## Jinja2 Templates

### Template Structure

```html
{% extends "base.html" %}

{% block title %}Invoices{% endblock %}

{% block content %}
<div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold mb-4">Invoices</h1>

    {% include "partials/_browser_invoices.html" %}
</div>
{% endblock %}
```

### Partials Naming

- `_browser_{entity}.html` - List/table views
- `_detail_{entity}.html` - Single item detail view
- `_new_{entity}.html` - Create form
- `_edit_{entity}.html` - Edit form
- `_row_{entity}.html` - Table row partial

### HTMX Attributes

```html
<!-- GET request -->
<button hx-get="/invoices/new" hx-target="#modal-content" hx-swap="innerHTML">
    New Invoice
</button>

<!-- POST request with form -->
<form hx-post="/invoices" hx-target="#invoice-list" hx-swap="afterbegin">
    ...
</form>

<!-- PATCH request -->
<form hx-patch="/invoices/{{ invoice.id }}" hx-target="#invoice-{{ invoice.id }}">
    ...
</form>

<!-- DELETE with confirmation -->
<button hx-delete="/invoices/{{ invoice.id }}"
        hx-confirm="Really delete this invoice?"
        hx-target="#invoice-{{ invoice.id }}"
        hx-swap="outerHTML">
    Delete
</button>
```

---

## Tailwind CSS + daisyUI

### Component Classes

```html
<!-- Buttons -->
<button class="btn btn-primary">Save</button>
<button class="btn btn-secondary">Cancel</button>
<button class="btn btn-error">Delete</button>

<!-- Forms -->
<input type="text" class="input input-bordered w-full" />
<textarea class="textarea textarea-bordered"></textarea>
<select class="select select-bordered w-full"></select>

<!-- Tables -->
<table class="table table-zebra">
    <thead>
        <tr>
            <th>Column</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Value</td>
        </tr>
    </tbody>
</table>

<!-- Cards -->
<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <h2 class="card-title">Title</h2>
        <p>Content</p>
    </div>
</div>
```

---

## German Error Messages

For user-facing validation errors, use German:

```python
raise ValueError("Betrag muss positiv sein")
raise ValueError("Datum darf nicht in der Zukunft liegen")
raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
```

---

## Documentation

### Module/Class Docstrings

```python
"""Brief one-line description.

Additional details if needed.
"""
```

### Function Docstrings

```python
def create_invoice(invoice_data: InvoiceCreate, db: Session) -> Invoice:
    """Create a new invoice.

    Args:
        invoice_data: Validated invoice creation data
        db: Database session

    Returns:
        Created Invoice instance with generated ID

    Raises:
        HTTPException: If validation fails
    """
```

### Comments

- **Explain WHY, not WHAT** - Code should speak for itself
- **No commented-out code** - Use version control
- **No TODOs without issue numbers** - Link to GitHub issues

---

## Testing

### Test Structure

```python
class TestInvoiceAPI:
    def test_create_invoice_success(self, client, db_session):
        """Test successful invoice creation."""

    def test_create_invoice_invalid_amount(self, client, db_session):
        """Test validation rejects negative amounts."""
```

### Fixtures

```python
@pytest.fixture
def db_session(test_db_engine):
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### Factory Pattern

```python
class InvoiceFactory(Factory):
    class Meta:
        model = Invoice

    counterparty_name = factory.Faker("company")
    direction = "incoming"
    gross_amount = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    invoice_date = factory.Faker("date_this_year")
```

---

## Quick Reference

| Element | Convention | Example |
|---------|------------|---------|
| Variables | snake_case | `invoice_total` |
| Functions | snake_case | `get_invoice()` |
| Classes | PascalCase | `InvoiceCreate` |
| Constants | UPPER_SNAKE | `MAX_AMOUNT` |
| Private | underscore | `_cached`, `__private` |
| Imports | Absolute from source | `from source.api.app import app` |
| Line length | 120 chars | - |
| Type hints | Always required | `def foo(x: int) -> str:` |

---

## Automation Commands

```bash
make format   # Black + isort
make lint     # Type checking + linting
make test     # Run tests with coverage
make dev      # Start dev server (port 8000)
make frontend-watch  # Tailwind CSS watch mode
```
