import sys
import json
from pathlib import Path
from datetime import datetime
from loguru import logger
from app.core.config import settings

def serialize(record):
    """Сериализация логов для JSON"""
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        "user": record["extra"].get("user", "system"),
        "request_id": record["extra"].get("request_id", None),
    }
    
    if record["exception"]:
        subset["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback.format(),
        }
    
    return json.dumps(subset)

def formatter(record):
    """Форматирование логов"""
    if settings.ENVIRONMENT == "production":
        return serialize(record) + "\n"
    else:
        # Человекочитаемый формат для разработки
        return "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>\n"

# Удаляем стандартный обработчик
logger.remove()

# Добавляем обработчики
log_path = Path("logs")
log_path.mkdir(exist_ok=True)

# Файл логов с ротацией
logger.add(
    log_path / "crm_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # Ротация в полночь
    retention="30 days",  # Храним 30 дней
    compression="zip",
    level="INFO",
    format=formatter,
    backtrace=True,
    diagnose=settings.DEBUG,
)

# Консоль для разработки
if settings.DEBUG:
    logger.add(
        sys.stderr,
        level="DEBUG",
        format=formatter,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

# JSON лог для продакшена
if settings.ENVIRONMENT == "production":
    logger.add(
        sys.stdout,
        level="INFO",
        format=formatter,
        serialize=True,
    )

# Middleware для логирования запросов
from fastapi import Request
import time
from uuid import uuid4

async def log_requests(request: Request, call_next):
    request_id = str(uuid4())
    
    with logger.contextualize(request_id=request_id):
        start_time = time.time()
        
        # Логируем входящий запрос
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Логируем ответ
            logger.info(
                "Request completed",
                status_code=response.status_code,
                process_time=f"{process_time:.3f}s",
            )
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            logger.error(
                "Request failed",
                error=str(e),
                process_time=f"{process_time:.3f}s",
                exc_info=True,
            )
            raise

# Декоратор для логирования функций
def log_function_call(func):
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.debug(
            f"Calling {func.__name__}",
            args=args,
            kwargs=kwargs,
        )
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(
                f"{func.__name__} completed",
                result_type=type(result).__name__,
            )
            return result
        except Exception as e:
            logger.error(
                f"{func.__name__} failed",
                error=str(e),
                exc_info=True,
            )
            raise
    
    return wrapper