"""Data Transfer routes for CSV export/import.

This router provides endpoints for exporting and importing time entries
via CSV files for data migration and backup/restore functionality.
"""

import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy import extract
from sqlalchemy.orm import Session

from source.api.context import render_template
from source.api.dependencies import get_db
from source.database.models import TimeEntry
from source.services.data_transfer import ExportService, ImportService

router = APIRouter(tags=["data-transfer"])


@router.get("/export")
async def export_time_entries(
    request: Request,
    month: Annotated[int, Query(ge=1, le=12)],
    year: Annotated[int, Query()],
    user_id: Annotated[int, Query()] = 1,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Export time entries for a month as CSV file.

    Args:
        request: FastAPI request object
        month: Month to export (1-12)
        year: Year to export
        user_id: User ID to export entries for (defaults to 1)
        db: Database session

    Returns:
        StreamingResponse with CSV file attachment
    """
    # Query entries for the user and month
    entries = (
        db.query(TimeEntry)
        .filter(
            TimeEntry.user_id == user_id,
            extract("month", TimeEntry.work_date) == month,
            extract("year", TimeEntry.work_date) == year,
        )
        .order_by(TimeEntry.work_date)
        .all()
    )

    # Use ExportService to generate CSV
    service = ExportService()
    result = service.export_entries(entries, user_id, year, month)

    # Return streaming response with CSV attachment
    return StreamingResponse(
        io.BytesIO(result.content),
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
        },
    )


@router.post("/import")
async def import_time_entries(
    request: Request,
    file: Annotated[UploadFile, File()],
    dry_run: Annotated[bool, Query()] = False,
    skip_duplicates: Annotated[bool, Query()] = False,
    user_id: Annotated[int, Query()] = 1,
    db: Session = Depends(get_db),
):
    """Import time entries from CSV file.

    Supports both API (JSON) and HTMX (HTML) clients.

    Args:
        request: FastAPI request object
        file: Uploaded CSV file
        dry_run: Query param - if True, validate only without persisting (defaults to False)
        skip_duplicates: Query param - if True, skip entries for dates that already exist (defaults to False)
        user_id: Query param - User ID to assign imported entries to (defaults to 1)
        db: Database session

    Returns:
        HTMLResponse with import result partial for HTMX requests,
        JSON dict for API requests

    Raises:
        HTTPException: 422 if validation fails (API mode)
    """
    # Read file content
    content = await file.read()

    # Use ImportService to process the file
    service = ImportService()
    result = service.import_file(
        content=content,
        user_id=user_id,
        db=db,
        dry_run=dry_run,
        skip_duplicates=skip_duplicates,
    )

    # Check if request is from HTMX
    is_htmx = request.headers.get("HX-Request") == "true"

    # Build error list for both response types
    errors_list = [
        {"row_number": e.row_number, "field": e.field, "message": e.message, "code": e.code} for e in result.errors
    ]

    # Handle validation errors
    if not result.success:
        if is_htmx:
            html = render_template(
                request,
                "partials/_import_result.html",
                success=False,
                errors=errors_list,
            )
            return HTMLResponse(content=html, status_code=422)
        else:
            raise HTTPException(
                status_code=422,
                detail={"success": False, "errors": errors_list},
            )

    # Return success response
    if is_htmx:
        html = render_template(
            request,
            "partials/_import_result.html",
            success=True,
            imported_count=result.imported_count,
            skipped_count=result.skipped_count,
        )
        response = HTMLResponse(content=html)
        response.headers["HX-Trigger"] = "timeEntriesImported"
        return response
    else:
        return {
            "success": True,
            "imported_count": result.imported_count,
            "skipped_count": result.skipped_count,
        }
