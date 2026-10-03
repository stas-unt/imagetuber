import tomllib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class AvatarPackage:
	""""""
	name: str
	author: str
	path: Path
	provides_emotions: bool
	emotions: list[str]
	faces: dict[str, Path]

	@classmethod
	def load(cls, package_dir: Path) -> Optional["AvatarPackage"]:
		""""""
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

		# Строим словарь путей к файлам
		face_paths = {}
		for key, rel_path in faces.items():
			full_path = package_dir / rel_path
			if not full_path.exists():
				print(f"[AvatarPackage] Файл не найден: {full_path}")
				return None
			face_paths[key] = full_path

		return cls(
			name=main["name"],
			author=main.get("author", "Неизвестен"),
			path=package_dir,
			provides_emotions=main.get("provides_emotions", False),
			emotions=main.get("emotions", []),
			faces=face_paths,
		)

def list_available_packages(avatars_dir: Path) -> list[AvatarPackage]:
	""""""
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
