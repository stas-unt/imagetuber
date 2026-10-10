from pathlib import Path
from PySide6.QtWidgets import QLabel, QWidget, QApplication, QVBoxLayout
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer

from settings import Settings, AVATARS_DIR
from avatar_package import AvatarPackage, Emotion, list_available_packages


class AvatarWindow(QWidget):
	def __init__(self, settings):
		super().__init__()
		self.settings = settings
		self.package: AvatarPackage | None = None
		self.current_emotion: str = "normal"
		self.is_speaking = False

		self.setWindowFlags(
			Qt.Window | Qt.FramelessWindowHint | Qt.Tool
		)
		self.setAttribute(Qt.WA_TranslucentBackground)

		icon_path = Path("res/img/icon.png")
		if icon_path.exists():
			self.setWindowIcon(QIcon(str(icon_path)))

		layout = QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

		self.eyes_label = QLabel(self)
		self.eyes_label.setScaledContents(True)
		self.eyes_label.setAlignment(Qt.AlignCenter)
		layout.addWidget(self.eyes_label)

		self.mouth_label = QLabel(self)
		self.mouth_label.setScaledContents(True)
		self.mouth_label.setAlignment(Qt.AlignCenter)
		layout.addWidget(self.mouth_label)

		self.blink_timer = QTimer(self)
		self.blink_timer.timeout.connect(self._blink)

		self.blink_close_timer = QTimer(self)
		self.blink_close_timer.setSingleShot(True)
		self.blink_close_timer.timeout.connect(self._open_eyes)

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
		print(f"[AvatarWindow] Доступные эмоции: {list(self.package.emotions.keys())}")

		if "normal" in self.package.emotions:
			self.current_emotion = "normal"
		else:
			self.current_emotion = list(self.package.emotions.keys())[0]

		self._update_display()
		self._setup_blink()

	def _update_display(self):
		if not self.package or self.current_emotion not in self.package.emotions:
			return

		emotion = self.package.emotions[self.current_emotion]

		pix = emotion.open if self.is_speaking else emotion.closed
		self.mouth_label.setPixmap(QPixmap(str(pix)))

		if self.package.eyes_open:
			self.eyes_label.setPixmap(QPixmap(str(self.package.eyes_open)))

		self.adjustSize()

	def _setup_blink(self):
		interval = self.settings.get("avatar", "blink_interval", 4.0)

		if self.package and self.package.eyes_open and self.package.eyes_closed:
			self.blink_timer.start(int(interval * 1000))
			print(f"[AvatarWindow] Моргание включено: каждые {interval} секунд")
		else:
			print(f"[AvatarWindow] Моргание отключено (нет изображений для глаз)")

	def _blink(self):
		if self.package and self.package.eyes_closed:
			self.eyes_label.setPixmap(QPixmap(str(self.package.eyes_closed)))

			duration = self.settings.get("avatar", "blink_duration", 0.15)
			self.blink_close_timer.start(int(duration * 1000))

	def _open_eyes(self):
		if self.package and self.package.eyes_open:
			self.eyes_label.setPixmap(QPixmap(str(self.package.eyes_open)))

	def set_speaking(self, speaking: bool):
		self.is_speaking = speaking
		self._update_display()

	def set_emotion(self, emotion_name: str):
		if self.package and emotion_name in self.package.emotions:
			self.current_emotion = emotion_name
			print(f"[AvatarWindow] Эмоция: {emotion_name}")
			self._update_display()

	def reload_package(self):
		"""Перезагружает пакет после его смены в настройках"""
		self._load_package()

	def get_emotions(self) -> list(str):
		"""Возвращает список доступных эмоций"""
		if self.package:
			return list(self.package.emotions.keys())
		return []
