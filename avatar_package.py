import tomllib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class Emotion:
	"""Эмоции"""
	name: str
	closed: Path
	open: Path

@dataclass
class AvatarPackage:
	"""Информация о пакете аватара"""
	name: str
	author: str
	path: Path
	provides_emotions: bool
	emotions: list[str]
	eyes_open: Optional[Path] = None
	eyes_closed: Optional[Path] = None

	@classmethod
	def load(cls, package_dir: Path) -> Optional["AvatarPackage"]:
		"""Загружает пакет из дериктории"""
		toml_path = package_dir / "avatar.toml"

		if not toml_path.exists():
			print(f"[AvatarPackage] Не найден avatar.toml в {package_dir}")
			return None

		try:
			with open(toml_path, "rb") as f:
				data = tomllib.load(f)
		except Exception as e:
			print(f"[AvatarPackage] Ошибка загрузки {toml_path}: {e}")
			return None

		main = data.get("main", {})
		faces = data.get("faces", {})

		# Проверяем обязательные поля
		if "name" not in main:
			print(f"[AvatarPackage] Отсутствует name в {toml_path}")
			return None

		emotions_dict = {}
		emotion_names = main.get("emotions", ["normal"])

		for emotion_name in emotion_names:
			closed_key = f"{emotion_name}_closed"
			open_key = f"{emotion_name}_open"

			if closed_key not in faces or open_key not in faces:
				print(f"[AvatarPackage] Отсутствуют файлы для эмоции '{emotion_name}'")
				continue

			closed_path = package_dir / faces[closed_key]
			open_path = package_dir / faces[open_key]

			if not closed_path.exists() or not open_path.exists():
				print(f"[AvatarPackage] Файлы не найдены для эмоции '{emotion_name}'")
				continue

			emotions_dict[emotion_name] = Emotion(
				name=emotion_name,
				closed=closed_path,
				open=open_path,
			)

		if not emotions_dict:
			print(f"[AvatarPackage] Не найдено ни одной эмоции в {package_dir}")
			return None

		eyes_open = None
		eyes_closed = None

		if "eyes_open" in faces:
			eyes_open_path = package_dir / faces["eyes_open"]
			if eyes_open_path.exists():
				eyes_open = eyes_open_path

		if "eyes_closed" in faces:
			eyes_closed_path = package_dir / faces["eyes_closed"]
			if eyes_closed_path.exists():
				eyes_closed = eyes_closed_path

		return cls(
			name=main["name"],
			author=main.get("author", "Неизвестен"),
			path=package_dir,
			provides_emotions=main.get("provides_emotions", False),
			emotions=emotions_dict,
			eyes_open=eyes_open,
			eyes_closed=eyes_closed,
		)

def list_available_packages(avatars_dir: Path) -> list[AvatarPackage]:
	"""Возвращает список всех доступных аватаров"""
	packages = []

	if not avatars_dir.exists():
		avatars_dir.mkdir(parents=True)
		return packages

	for item in avatars_dir.iterdir():
		if item.is_dir():
			pkg = AvatarPackage.load(item)
			if pkg:
				packages.append(pkg)

	return packages
