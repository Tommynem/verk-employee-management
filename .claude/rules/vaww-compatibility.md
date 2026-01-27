# VaWW Compatibility Requirements

Verk Bookkeeping is designed to eventually become a **paid addon** for VaWW (the main business management application). This rule documents compatibility requirements for future integration.

## Integration Strategy

### Current Status

- **Standalone Application**: Own SQLite database, no tight coupling
- **Future State**: Paid addon integrated into VaWW
- **Design Philosophy**: Keep compatible now, integrate later

### Loose Coupling Approach

**Customer References**:
- Store `vaww_customer_id` as integer (no FK enforcement)
- No direct database relationships to VaWW tables
- Future API client will fetch VaWW customer details when needed

**Separate Database**:
- Own SQLite database for all bookkeeping data
- No foreign keys pointing to VaWW database
- Portable and independently testable

---

## VaWW Component Reuse

### Reuse Production-Grade Components

**Principle**: Copy production-ready components from VaWW main app via filesystem instead of rebuilding from scratch.

**VaWW Main App Location**: `/Users/tomge/Documents/Git/vaww/the_great_rewiring`

**Component Locations**:
- Templates: `templates/web/components/`
- Macros: `templates/web/macros/`
- Base template: `templates/web/base.html`

**Copy Pattern**:
```bash
# Copy component from VaWW to extension
cp /Users/tomge/Documents/Git/vaww/the_great_rewiring/templates/web/components/_modal_confirm_delete.html \
   templates/components/
```

**When to Copy**:
- Component exists in VaWW and solves the same problem
- Component is generalized (not customer/order specific)
- Visual consistency with main app is important
- Production-ready quality is needed immediately

**Examples of Reusable Components**:
- Error pages (404.html, 500.html)
- Modal templates (delete confirmation, discard confirmation)
- Form macros and input patterns
- Table/browser view patterns
- Toast notification system
- Icon macros

**Adaptation Guidelines**:
- Copy component as-is first
- Modify only what's necessary for extension-specific needs
- Maintain visual consistency with VaWW
- Extension should feel like part of VaWW, not a separate app

---

## Template Compatibility

### VaWW Template Matching

When user specifies a component will be reused, keep it equivalent or VERY close to the main-app components.

**Use filesystem copy** for local VaWW access (preferred):
```bash
cp /Users/tomge/Documents/Git/vaww/the_great_rewiring/templates/web/path/to/file templates/
```

**Use GitHub CLI** for remote access if needed:
```bash
gh api repos/Tommynem/VaWW/contents/templates/path/to/file -q '.content' | base64 -d
```

### Template Naming Convention (Match VaWW)

- Browser views: `_browser_{entity}.html`
- Detail views: `_detail_{entity}.html`
- Forms: `_new_{entity}.html`
- Partials: `partials/_*.html`

### Base Template Structure

- Match VaWW `base.html` structure
- Use same macro patterns
- Same component structure (buttons, forms, tables)
- Consistent navigation patterns

### HTMX Patterns

Match VaWW HTMX conventions:
- `hx-get`, `hx-post`, `hx-patch`, `hx-delete` for CRUD
- `hx-swap="innerHTML"` for partial updates
- `hx-target` for specifying target elements
- `hx-trigger` for event handling
- `HX-Trigger` response headers for events (e.g., `invoiceCreated`)

---

## Route Compatibility

### REST Route Patterns (Match VaWW)

| Route | Verb | Response | HX-Trigger |
|-------|------|----------|------------|
| `/{entities}` | GET | `_browser_{entity}.html` | - |
| `/{entities}/new` | GET | `_new_{entity}.html` | - |
| `/{entities}` | POST | `_detail_{entity}.html` | `{entity}Created` |
| `/{entities}/{id}` | GET | `_detail_{entity}.html` | - |
| `/{entities}/{id}` | PATCH | `_detail_{entity}.html` | `{entity}Updated` |
| `/{entities}/{id}` | DELETE | (empty/redirect) | `{entity}Deleted` |

### HTMX Response Pattern

```python
html = render_template(request, "partials/_detail_invoice.html", invoice=invoice)
response = HTMLResponse(content=html, status_code=201)
response.headers["HX-Trigger"] = "invoiceCreated"
return response
```

---

## Pydantic Schema Pattern (Match VaWW)

```python
class InvoiceUpdate(BaseModel):
    """Base with all fields and validators."""
    counterparty_name: str
    gross_amount: Decimal = Field(ge=Decimal("0.01"))

class InvoiceCreate(InvoiceUpdate):
    """Inherits all from Update."""
    direction: Literal["incoming", "outgoing"]

class InvoiceResponse(InvoiceUpdate):
    """Adds database fields."""
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

---

## Styling Compatibility

### Tailwind CSS + daisyUI

- Use same daisyUI component classes as VaWW
- Consistent button styles (btn, btn-primary, btn-secondary)
- Same form input patterns (input, textarea, select)
- Matching table styles (table, table-zebra)
- Consistent color scheme alignment

### CSS Variables

If VaWW uses CSS custom properties for theming, maintain compatibility for eventual integration.

---

## VaWW Compatibility Checklist

**Before Creating Templates**:

- [ ] Match VaWW `base.html` structure
- [ ] Use same macro patterns
- [ ] Same component structure

**Template Naming**:

- [ ] Browser views: `_browser_{entity}.html`
- [ ] Detail views: `_detail_{entity}.html`
- [ ] Forms: `_new_{entity}.html`

**Route Compliance**:

- [ ] Same HTTP verbs (GET/POST/PATCH/DELETE)
- [ ] Same response types (HTMLResponse)
- [ ] Same HX-Trigger header pattern

**Schema Compliance**:

- [ ] Update -> Create -> Response inheritance pattern
- [ ] Proper Field validators
- [ ] ConfigDict with from_attributes=True for responses

---

## What's Reusable from VaWW (Invest Upfront)

- Templates (user-facing, HTMX coupled)
- Pydantic Schemas (API contracts)
- Route structure (templates hardcode paths)
- HTMX patterns
- Template naming convention

## What's Simplified (Skip for Now)

- ServiceContainer (skip until 3+ injectable services)
- Repository interfaces (skip until need polymorphism)
- OperationResult (skip until complex error handling)
- UnitOfWork (skip until multi-entity transactions)

---

## Testing VaWW Compatibility

When making changes that affect UI/API:

1. Verify template structure matches VaWW patterns
2. Test HTMX interactions work as expected
3. Confirm route patterns follow convention
4. Check Pydantic schema inheritance

**Note**: Playwright browser testing is useful for verifying features work, but uses large amounts of context. Always outsource this to an agent if needed. Use it after implementing substantial functionality.
