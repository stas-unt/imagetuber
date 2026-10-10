import os
import tomllib
from pathlib import Path

try:
	import tomli_w
except ImportError:
	tomli_w = None


CONFIG_FILE = Path("config.toml")
AVATARS_DIR = Path("avatars")

DEFAULT_CONFIG = {
	"audio": {
		"device": "default",
		"sample_rate": 48000,
		"block_size": 1024,
		"silence_threshold": 0.02,
		"hysteresis": 0.7,
		"calibration_multiplier": 2.0,
	},
	"avatar": {
		"package": "default",
		"blink_interval": 6.0,
		"blink_duration": 0.15,
	},
}


class Settings:
	"""Загрузка и сохранение настроек из TOML"""

	def __init__(self):
		self.config = self._load_or_create()

	def _load_or_create(self) -> dict:
		if not CONFIG_FILE.exists():
			self._save_default()
			return DEFAULT_CONFIG.copy()

		with open(CONFIG_FILE, "rb") as f:
			loaded = tomllib.load(f)

		# Дополняем недостающими ключами
		for section, values in DEFAULT_CONFIG.items():
			if section not in loaded:
				loaded[section] = value.copy()
			else:
				for key, value in values.items():
					if key not in loaded[section]:
						loaded[section][key] = value

		return loaded

	def _save_default(self):
		if tomli_w is None:
			# Если tomli_w не установлен, то просто создаем файл текстом
			with open(CONFIG_FILE, "w", encoding="utf-8") as f:
				f.write(self._config_to_toml(DEFAULT_CONFIG))
		else:
			with open(CONFIG_FILE, "wb") as f:
				tomli_w.dump(DEFAULT_CONFIG, f)

	def _config_to_toml(self, config: dict) -> str:
		"""Простой сериализатор, если tomli_w не установлен"""
		lines = []
		for section, values in config.items():
			lines.append(f"[{section}]")
			for key, value in values.items():
				if isinstance(value, str):
					lines.append(f'{key} = "{value}"')
				elif isinstance(value, bool):
					lines.append(f"{key} = {str(value).lower()}")
				else:
					lines.append(f"{key} = {value}")
			lines.append("")
		return "\n".join(lines)

	def save(self):
		"""Сохранить текущие настройки в файл"""
		if tomli_w is None:
			with open(CONFIG_FILE, "w", encoding="utf-8") as f:
				f.write(self._config_to_toml(self.config))
		else:
			with open(CONFIG_FILE, "wb") as f:
				tomli_w.dump(self.config, f)

	def get(self, section: str, key: str, default=None):
		"""Получить значение, с поддержкой вложенных default из DEFAULT_CONFIG"""
		value = self.config.get(section, {}).get(key)
		if value is None:
			value = DEFAULT_CONFIG.get(section, {}).get(key, default)
		return value

	def set(self, section: str, key: str, value):
		if section not in self.config:
			self.config[section] = {}
		self.config[section][key] = value
