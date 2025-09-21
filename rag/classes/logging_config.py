"""
Настройки логирования для визуального разделения логов.
"""

import logging
import sys
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Форматтер с цветовой подсветкой для разных уровней логирования."""

    # ANSI цветовые коды
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    # Эмодзи для разных уровней
    EMOJIS = {
        "DEBUG": "🔍",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "💥",
    }

    def format(self, record):
        # Добавляем эмодзи и цвет
        emoji = self.EMOJIS.get(record.levelname, "")
        color = self.COLORS.get(record.levelname, "")
        reset = self.COLORS["RESET"]

        # Форматируем сообщение
        record.levelname = f"{color}{emoji} {record.levelname}{reset}"
        record.msg = f"{color}{record.msg}{reset}"

        return super().format(record)


def setup_logging(
    level: str = "INFO",
    use_colors: bool = True,
    show_timestamps: bool = True,
    show_module: bool = False,
) -> None:
    """
    Настраивает логирование с визуальным разделением.

    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_colors: Использовать цветовую подсветку
        show_timestamps: Показывать временные метки
        show_module: Показывать имя модуля
    """
    # Создаем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Очищаем существующие обработчики
    root_logger.handlers.clear()

    # Создаем обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Настраиваем формат
    format_parts = []
    if show_timestamps:
        format_parts.append("%(asctime)s")
    if show_module:
        format_parts.append("[%(name)s]")
    format_parts.append("%(levelname)s")
    format_parts.append("%(message)s")

    format_string = " | ".join(format_parts)

    if use_colors:
        formatter: logging.Formatter = ColoredFormatter(format_string)
    else:
        formatter = logging.Formatter(format_string)

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Настраиваем логирование для внешних библиотек
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Получает логгер с заданным именем."""
    return logging.getLogger(name)


# Пример использования
if __name__ == "__main__":
    # Настраиваем логирование
    setup_logging(level="DEBUG", use_colors=True, show_timestamps=True)

    # Тестируем
    logger = get_logger(__name__)

    logger.debug("Это отладочное сообщение")
    logger.info("Это информационное сообщение")
    logger.warning("Это предупреждение")
    logger.error("Это ошибка")
    logger.critical("Это критическая ошибка")
