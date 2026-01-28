"""FastAPI application for Verk Employee Management Extension."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import routers
from source.api.routers import settings, summaries, time_entries

app = FastAPI(
    title="Verk Zeiterfassung",
    description="Internal employee management tool for time tracking",
    version="0.1.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates for error pages
templates = Jinja2Templates(directory="templates")


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: StarletteHTTPException) -> Response:
    """Handle 404 Not Found errors for non-existent routes.

    Only handles routing 404s (when no route matches). HTTPExceptions raised
    within route handlers are passed through with their JSON detail.

    Args:
        request: FastAPI request object
        exc: Exception that was raised

    Returns:
        HTML response with 404 error page or JSON response for API errors
    """
    # If exception has a detail attribute and it's not the default routing message,
    # it was raised by a route handler - return JSON response
    if hasattr(exc, "detail") and exc.detail != "Not Found":
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    # Otherwise, it's a routing 404 - return HTML error page
    return templates.TemplateResponse("pages/404.html", {"request": request}, status_code=404)


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
