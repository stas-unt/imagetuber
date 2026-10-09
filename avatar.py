from pathlib import Path
from PySide6.QtWidgets import QLabel, QWidget, QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Signal

from settings import Settings, AVATARS_DIR
from avatar_package import AvatarPackage, list_available_packages


class AvatarWindow(QWidget):
	position_changed = Signal(int, int)

	def __init__(self, settings):
		super().__init__()
		self.settings = settings
		self.package: AvatarPackage | None = None

		self.setWindowFlags(
			Qt.Window | Qt.FramelessWindowHint | Qt.Tool
		)
		self.setAttribute(Qt.WA_TranslucentBackground)

		icon_path = Path("res/img/icon.png")
		if icon_path.exists():
			self.setWindowIcon(QIcon(str(icon_path)))

		self.label = QLabel(self)
		self.label.setScaledContents(True)

		self._load_package()

	def _load_package(self):
		"""Загружает активный пакет лиц."""
		package_name = self.settings.get("avatar", "package")
		package_dir = AVATARS_DIR / package_name

		packages = list_available_packages(AVATARS_DIR)

		for pkg in packages:
			if pkg.name == package_name or pkg.path.name == package_name:
				self.package = pkg
				break

		if not self.package:
			if packages:
				self.package = packages[0]
				print(f"[AvatarWindow] Пакет '{package_name}' не найден, "
						f"использую '{self.package.name}'")
			else:
				raise FileNotFoundError(
					f"Не найдено ни одного пакета аватаров в {AVATARS_DIR}"
				)

		print(f"[AvatarWindow] Загружен пакет: {self.package.name} "
				f"(автор: {self.package.author})")

		# Загружаем картинки
		# TODO: Загрузка картинок в зависимости от значения emotion
		self.pix_closed = QPixmap(str(self.package.faces.get("normal_closed")))
		self.pix_open = QPixmap(str(self.package.faces.get("normal_open")))

		if self.pix_closed.isNull() or self.pix_open.isNull():
			raise FileNotFoundError(
					f"В пакете '{self.package.name}' отсутствуют "
					f"normal_closed.png/normal_open.png"
				)

		self.label.setPixmap(self.pix_closed)
		self.resize(self.pix_closed.size())

		screen = QApplication.primaryScreen().geometry()
		self.move(screen.width() - self.width() - 50,
					screen.height() - self.height() - 150)

	def set_speaking(self, speaking: bool):
		self.label.setPixmap(self.pix_open if speaking else self.pix_closed)

	def reload_package(self):
		"""Перезагружает пакет после его смены в настройках"""
		self._load_package()
