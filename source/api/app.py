"""FastAPI application for Verk Employee Management Extension."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import routers
from source.api.routers import data_transfer, settings, summaries, time_entries

app = FastAPI(
    title="Verk Zeiterfassung",
    description="Internal employee management tool for time tracking",
    version="0.1.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates for error pages
templates = Jinja2Templates(directory="templates")


def is_browser_request(request: Request) -> bool:
    """Check if request is from a browser based on Accept header.

    Args:
        request: FastAPI request object

    Returns:
        True if request accepts HTML (browser), False otherwise (API)
    """
    accept = request.headers.get("accept", "")
    return "text/html" in accept


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: StarletteHTTPException) -> Response:
    """Handle 404 Not Found errors with content negotiation.

    Args:
        request: FastAPI request object
        exc: Exception that was raised

    Returns:
        HTML response for browser requests, JSON for API requests
    """
    # Get error message from exception detail or use default German message
    error_message = (
        exc.detail
        if hasattr(exc, "detail") and exc.detail != "Not Found"
        else "Die angeforderte Ressource wurde nicht gefunden"
    )

    # Browser requests get HTML error page
    if is_browser_request(request):
        return templates.TemplateResponse(
            "pages/404.html", {"request": request, "error_message": error_message}, status_code=404
        )

    # API requests get JSON
    return JSONResponse(status_code=404, content={"detail": error_message})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
    """Handle HTTPException with content negotiation.

    Args:
        request: FastAPI request object
        exc: HTTP exception

    Returns:
        HTML response for browser requests, JSON for API requests
    """
    # Browser requests get HTML error page
    if is_browser_request(request):
        error_message = exc.detail if exc.detail else "Ein Fehler ist aufgetreten"

        # Choose template based on status code
        if exc.status_code == 404:
            template = "pages/404.html"
            if not exc.detail or exc.detail == "Not Found":
                error_message = "Die angeforderte Ressource wurde nicht gefunden"
        elif exc.status_code == 422:
            template = "pages/422.html"
        else:
            # For other errors, use generic error page or 500
            template = "pages/500.html"

        return templates.TemplateResponse(
            template, {"request": request, "error_message": error_message}, status_code=exc.status_code
        )

    # API requests get JSON
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> Response:
    """Handle 422 Unprocessable Entity validation errors with content negotiation.

    Args:
        request: FastAPI request object
        exc: Validation error exception

    Returns:
        HTML response for browser requests, JSON for API requests
    """
    # Browser requests get HTML error page
    if is_browser_request(request):
        # Extract first validation error for display
        error_details = exc.errors()
        error_message = "Ungültige Anfrageparameter"
        if error_details:
            # Format: "field: error message"
            first_error = error_details[0]
            field = first_error.get("loc", ["unknown"])[-1]
            msg = first_error.get("msg", "")
            error_message = f"Ungültiger Wert für '{field}': {msg}"

        return templates.TemplateResponse(
            "pages/422.html", {"request": request, "error_message": error_message}, status_code=422
        )

    # API requests get JSON (FastAPI default format)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception) -> HTMLResponse:
    """Handle 500 Internal Server Error.

    Args:
        request: FastAPI request object
        exc: Exception that was raised

    Returns:
        HTML response with 500 error page
    """
    return templates.TemplateResponse("pages/500.html", {"request": request}, status_code=500)


# Include routers
app.include_router(data_transfer.router, prefix="/time-entries")
app.include_router(time_entries.router)
app.include_router(summaries.router)
app.include_router(settings.router)


@app.get("/")
async def root():
    """Redirect root to time entries page for current month."""
    from datetime import date

    from fastapi.responses import RedirectResponse

    today = date.today()
    return RedirectResponse(url=f"/time-entries?month={today.month}&year={today.year}", status_code=302)


@app.get("/api/health")
def health_check() -> dict:
    """Health check endpoint for monitoring.

    Returns:
        Dict with status indicator

    Example:
        GET /api/health
        Response: {"status": "ok"}
    """
    return {"status": "ok"}
