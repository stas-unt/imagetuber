import logging
import zipfile
import shutil

from pathlib import Path
from datetime import datetime


LOGS_DIR = Path("logs")
LATEST_LOG = LOGS_DIR / "latest.log"
ERROR_LOG = LOGS_DIR / "error.log"

def _archieve_old_log(log_path: Path):

	if not log_path.exists() or log_path.stat().st_size == 0:
		return

	timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
	archieve_name = f"{log_path.stem}_{timestamp}.zip"
	archieve_path = LOGS_DIR / archieve_name

	try:
		with zipfile.ZipFile(archieve_path, "w", zipfile.ZIP_DEFLATED) as zf:
			zf.write(log_path, arcname=log_path.name)
		log_path.unlink()
		print(f"[Logger] Архивирован {archieve_name}")
	except Exception as e:
		print(f"[Logger] Ошибка архивации {log_path}: {e}")


def setup_logger(name: str = "imagetuber") -> logging.Logger:
	"""Настраивает и возвращает логгер"""
	# Создаем папку логов
	LOGS_DIR.mkdir(parents=True, exist_ok=True)

	# Архивируем старые логи
	_archieve_old_log(LATEST_LOG)
	_archieve_old_log(ERROR_LOG)

	# Создаем логгер
	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG)

	# Очищаем старые хендлеры (на случай повторного вызова)
	logger.handlers.clear()

	# Формат сообщений
	formatter = logging.Formatter(
		"[%(asctime)s] [%(levelname)s] [%(name)s.%(module)s] %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S"
	)

	# Хэндлер для latest.log
	latest_handler = logging.FileHandler(LATEST_LOG, encoding="utf-8")
	latest_handler.setLevel(logging.DEBUG)
	latest_handler.setFormatter(formatter)
	logger.addHandler(latest_handler)

	# Хэндлер для error.log
	error_handler = logging.FileHandler(ERROR_LOG, encoding="utf-8")
	error_handler.setLevel(logging.ERROR)
	error_handler.setFormatter(formatter)
	logger.addHandler(error_handler)

	# Хэндлер для консоли
	console_handler = logging.StreamHandler()
	console_handler.setLevel(logging.INFO)
	console_handler.setFormatter(formatter)
	logger.addHandler(console_handler)

	return logger

logger = setup_logger()
