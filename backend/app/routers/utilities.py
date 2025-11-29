"""Utilities router for reports, exports, debts, and receipt scanning."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import date
import io
import logging

from app.utils.auth import get_current_user
from app.services.utilities_service import get_utilities_service, UtilitiesService
from app.models.utility import (
    DebtEntry,
    DebtResponse,
    DebtUpdate,
    DebtType,
    NetWorthData,
    ReportType,
    ReportFormat,
    ReportRequest,
    ReceiptScanResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/utilities", tags=["utilities"])


# ==================== DEBT MANAGEMENT ====================

@router.post("/debt", response_model=DebtResponse)
async def create_debt(
    debt_data: DebtEntry,
    current_user: dict = Depends(get_current_user),
    utilities_service: UtilitiesService = Depends(get_utilities_service)
):
    """
    Create a new debt entry.
    
    Track money you owe to someone or money someone owes to you.
    """
    try:
        user_id = current_user["uid"]
        return await utilities_service.create_debt(user_id, debt_data)
    except Exception as e:
        logger.error(f"Error creating debt: {e}")
        raise HTTPException(status_code=500, detail="Failed to create debt entry")


@router.get("/debt", response_model=List[DebtResponse])
async def get_debts(
    debt_type: Optional[DebtType] = None,
    current_user: dict = Depends(get_current_user),
    utilities_service: UtilitiesService = Depends(get_utilities_service)
):
    """
    Get all debt entries.
    
    Optionally filter by type (owed/lent).
    """
    try:
        user_id = current_user["uid"]
        return await utilities_service.get_debts(user_id, debt_type)
    except Exception as e:
        logger.error(f"Error getting debts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get debt entries")


@router.put("/debt/{debt_id}", response_model=DebtResponse)
async def update_debt(
    debt_id: str,
    update_data: DebtUpdate,
    current_user: dict = Depends(get_current_user),
    utilities_service: UtilitiesService = Depends(get_utilities_service)
):
    """
    Update a debt entry.
    
    Can update amount, status, paid amount, etc.
    """
    try:
        user_id = current_user["uid"]
        result = await utilities_service.update_debt(user_id, debt_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Debt entry not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating debt: {e}")
        raise HTTPException(status_code=500, detail="Failed to update debt entry")


@router.put("/debt/{debt_id}/mark-paid", response_model=DebtResponse)
async def mark_debt_paid(
    debt_id: str,
    current_user: dict = Depends(get_current_user),
    utilities_service: UtilitiesService = Depends(get_utilities_service)
):
    """
    Mark a debt as fully paid.
    """
    try:
        user_id = current_user["uid"]
        result = await utilities_service.mark_debt_paid(user_id, debt_id)
        if not result:
            raise HTTPException(status_code=404, detail="Debt entry not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking debt as paid: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark debt as paid")


@router.delete("/debt/{debt_id}")
async def delete_debt(
    debt_id: str,
    current_user: dict = Depends(get_current_user),
    utilities_service: UtilitiesService = Depends(get_utilities_service)
):
    """
    Delete a debt entry.
    """
    try:
        user_id = current_user["uid"]
        success = await utilities_service.delete_debt(user_id, debt_id)
        if not success:
            raise HTTPException(status_code=404, detail="Debt entry not found")
        return {"success": True, "message": "Debt entry deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting debt: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete debt entry")


# ==================== NET WORTH ====================

@router.get("/networth", response_model=NetWorthData)
async def get_net_worth(
    current_user: dict = Depends(get_current_user),
    utilities_service: UtilitiesService = Depends(get_utilities_service)
):
    """
    Calculate and return user's net worth.
    
    Assets (balance + receivables) - Liabilities (payables)
    """
    try:
        user_id = current_user["uid"]
        return await utilities_service.calculate_net_worth(user_id)
    except Exception as e:
        logger.error(f"Error calculating net worth: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate net worth")


# ==================== REPORTS ====================

@router.post("/reports")
async def generate_report(
    report_request: ReportRequest,
    current_user: dict = Depends(get_current_user),
    utilities_service: UtilitiesService = Depends(get_utilities_service)
):
    """
    Generate a financial report (PDF or CSV).
    
    Includes AI-powered summary and analysis.
    """
    try:
        user_id = current_user["uid"]
        file_bytes, filename = await utilities_service.generate_report(user_id, report_request)
        
        # Determine content type
        if report_request.format == ReportFormat.PDF:
            media_type = "application/pdf"
        else:
            media_type = "text/csv"
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


@router.get("/reports")
async def get_report(
    report_type: ReportType = Query(default=ReportType.MONTHLY),
    report_format: ReportFormat = Query(default=ReportFormat.PDF, alias="format"),
    month: Optional[int] = Query(default=None, ge=1, le=12),
    year: Optional[int] = Query(default=None, ge=2000, le=2100),
    current_user: dict = Depends(get_current_user),
    utilities_service: UtilitiesService = Depends(get_utilities_service)
):
    """
    Generate a financial report via GET request.
    
    Args:
        type: Report type (monthly/annual)
        format: Output format (pdf/csv)
        month: Month for monthly report (1-12)
        year: Year for the report
    """
    try:
        user_id = current_user["uid"]
        
        report_request = ReportRequest(
            type=report_type,
            format=report_format,
            month=month,
            year=year,
            include_charts=True,
            include_categories=True,
            include_goals=True
        )
        
        file_bytes, filename = await utilities_service.generate_report(user_id, report_request)
        
        media_type = "application/pdf" if report_format == ReportFormat.PDF else "text/csv"
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


# ==================== EXPORT ====================

@router.get("/export")
async def export_transactions(
    format: ReportFormat = Query(default=ReportFormat.CSV),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    categories: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    utilities_service: UtilitiesService = Depends(get_utilities_service)
):
    """
    Export transactions to CSV or PDF.
    
    Args:
        format: Export format (csv/pdf)
        start_date: Filter start date
        end_date: Filter end date
        categories: Comma-separated category filter
    """
    try:
        user_id = current_user["uid"]
        
        # Parse categories
        category_list = None
        if categories:
            category_list = [c.strip() for c in categories.split(",")]
        
        file_bytes, filename = await utilities_service.export_transactions(
            user_id, format, start_date, end_date, category_list
        )
        
        media_type = "application/pdf" if format == ReportFormat.PDF else "text/csv"
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error exporting transactions: {e}")
        raise HTTPException(status_code=500, detail="Failed to export transactions")


# ==================== RECEIPT SCANNING ====================

def _validate_image_magic_bytes(image_bytes: bytes) -> bool:
    """Validate image type by checking magic bytes (file signature)."""
    if len(image_bytes) < 8:
        return False
    
    # JPEG magic bytes: FF D8 FF
    if image_bytes[:3] == b'\xff\xd8\xff':
        return True
    
    # PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return True
    
    return False


@router.post("/receipt-scan", response_model=ReceiptScanResponse)
async def scan_receipt(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    utilities_service: UtilitiesService = Depends(get_utilities_service)
):
    """
    Scan a receipt image and extract transaction data using AI.
    
    Supported formats: JPEG, PNG
    Returns extracted merchant, amount, date, items, and suggested category.
    """
    from app.config.constants import (
        ALLOWED_RECEIPT_MIME_TYPES,
        MAX_RECEIPT_FILE_SIZE_BYTES,
        MAX_RECEIPT_FILE_SIZE_MB,
    )
    
    try:
        # Validate declared content type
        if file.content_type not in ALLOWED_RECEIPT_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only JPEG and PNG images are supported."
            )
        
        # Read file bytes
        image_bytes = await file.read()
        
        # Check file size
        if len(image_bytes) > MAX_RECEIPT_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {MAX_RECEIPT_FILE_SIZE_MB}MB."
            )
        
        # Validate actual file content via magic bytes (prevents spoofed content-type)
        if not _validate_image_magic_bytes(image_bytes):
            raise HTTPException(
                status_code=400,
                detail="Invalid image file. File content does not match a valid JPEG or PNG image."
            )
        
        # Validate actual image content using PIL to prevent malicious files with fake MIME types
        try:
            import PIL.Image
            from io import BytesIO
            # Open and verify the image header
            with PIL.Image.open(BytesIO(image_bytes)) as image:
                # Access image properties to ensure it's a valid image format
                _ = image.format
                _ = image.size
        except (PIL.Image.UnidentifiedImageError, PIL.Image.DecompressionBombError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file. The file could not be processed as an image."
            )
        
        user_id = current_user["uid"]
        return await utilities_service.scan_receipt(user_id, image_bytes)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning receipt: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan receipt")


# ==================== MANUAL TRANSACTION ====================

@router.post("/manual-transaction")
async def create_manual_transaction(
    current_user: dict = Depends(get_current_user)
):
    """
    Create a manual transaction entry.
    
    This redirects to the main transactions endpoint.
    Use POST /transactions instead for better functionality.
    """
    raise HTTPException(
        status_code=307,
        detail="Use POST /transactions endpoint",
        headers={"Location": "/transactions"}
    )
