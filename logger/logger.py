"""
Basic logging utility

Provides two API functionalities:
@log_function_call decorator - automatically logs function calls with arguments and return values
logger.debug/info/warning/error/critical methods - custom log messages

Logs are displayed in color on the console and saved in JSON Lines format to a log file.

Example usage:
    from logger.logger import logger, log_function_call

    @log_function_call()
    def my_function(param1, param2):
        logger.info("This is an info message")

    my_function("value1", "value2")


The log file will contain entries like:
{"timestamp": "2024-06-01T12:00:00+0000", "level": "INFO", "filename":
"my_script.py", "lineno": 10, "message": "This is an info message", "logger":
"myapp"}

"""

import atexit
import functools
import json
import logging
import logging.handlers
import os
import queue
import traceback


class ColoredFormatter(logging.Formatter):
    """Formatter that adds color codes to log levels for console output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"  # Reset color

    def format(self, record):
        if record.levelname in self.COLORS:
            # Create a copy of the record to avoid modifying the original
            colored_record = logging.makeLogRecord(record.__dict__)
            colored_record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
            return super().format(colored_record)
        return super().format(record)


class JSONLinesFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "filename": record.filename,
            "lineno": record.lineno,
            "message": record.getMessage(),
            "logger": record.name,
        }
        return json.dumps(log_record, default=str)


def setup_logging(
    log_file_path: str = "logger/logs/log.jsonl", log_level=logging.DEBUG
) -> logging.Logger:
    """
    Set up logging with both console and file output using QueueHandler/QueueListener.

    Args:
        log_file_path: Path to the log file
        log_level: Minimum log level (default: DEBUG)
    """
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    logger_instance = logging.getLogger("myapp")
    logger_instance.setLevel(log_level)

    logger_instance.handlers.clear()

    log_queue = queue.Queue(maxsize=-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)
    logger_instance.addHandler(queue_handler)
    logger_instance.propagate = False

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = ColoredFormatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s] %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONLinesFormatter())

    listener = logging.handlers.QueueListener(
        log_queue, console_handler, file_handler, respect_handler_level=True
    )
    listener.start()

    atexit.register(listener.stop)

    is_production: bool = (
        os.getenv("ENVIRONMENT", "development").lower() == "production"
    )

    sqlalchemy_log_level = logging.WARNING if is_production else logging.INFO

    sqlalchemy_logger_names = [
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
        "sqlalchemy.orm",
    ]

    for sqlalchemy_logger_name in sqlalchemy_logger_names:
        sqlalchemy_logger: logging.Logger = logging.getLogger(sqlalchemy_logger_name)
        sqlalchemy_logger.setLevel(sqlalchemy_log_level)

    return logger_instance


logger = setup_logging()


def log_function_call(logger_instance=None):
    logger_instance = logger_instance or logger

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            function_name = function.__name__
            logger_instance.debug(
                f"\n Function call: '{function_name}'\n"
                f"   ├─ args:   {args}\n"
                f"   └─ kwargs: {kwargs}"
            )
            try:
                result = function(*args, **kwargs)
                logger_instance.debug(
                    f"\n Function '{function_name}' \n" f" returned: {result}"
                )
                return result
            except Exception as e:
                logger_instance.exception(
                    f"Function {function_name} raised {type(e).__name__}: {e}\n{traceback.format_exc()}"
                )
                raise

        return wrapper

    return decorator
