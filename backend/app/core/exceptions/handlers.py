import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions.base import LinkupError

logger = logging.getLogger("linkup")

# שים לב: הורדתי את הגרשיים מה-LinkupError בפרמטר exc
async def linkup_exception_handler(request: Request, exc: LinkupError):
    """
    Handler מרכזי שתופס את כל סוגי השגיאות שלנו
    """
    # תיעוד השגיאה בלוגים
    # ה-f-string משתמש בערכים שקיימים בתוך האובייקט exc
    logger.error(
        f"🚨 Error: {exc.error_code} | Trace: {exc.trace_id} | Message: {exc.message}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.message,
            "error_code": exc.error_code,
            "trace_id": exc.trace_id,
            "details": exc.payload
        }
    )