from functools import wraps
import logging
from fastapi import HTTPException
from typing import Any, Callable

from fastapi.responses import JSONResponse


def handle_errors(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.error(f'Error in {func.__name__}: {str(e)}')
            return  HTTPException(status_code=400, 
                                detail=str(e)
                                )
    return wrapper