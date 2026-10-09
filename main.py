import sys
import signal
import pdb
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QMessageBox, QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QDoubleSpinBox, QTabWidget, QTextEdit, QWidget)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QTimer, Qt

# Свои Библиотеки
from settings import Settings, AVATARS_DIR
from audio import AudioThread, get_audio_input_devices
from avatar import AvatarWindow
from avatar_package import list_available_packages


APP_NAME = "ImageTuber"
APP_VERSION = "0.3.0"
APP_DESCRIPTION = "Виртуальный аватар, которому не требуется камера. Только микрофон."
ICON_PATH = Path("res/img/icon.png")


class SettingsDialog(QDialog):
	"""Диалог настроек."""

	def __init__(self, settings: Settings, parent=None):
		super().__init__(parent)
		self.settings = settings
		self.setWindowTitle("Настройки - ImageTuber")
		self.setMinimumWidth(400)

		layout = QVBoxLayout(self)

		# --- Аудио ---
		layout.addWidget(QLabel("<b>Аудио</b>"))

		# Выпадающий список устройств
		h1 = QHBoxLayout()
		h1.addWidget(QLabel("Устройство:"))
		self.device_combo = QComboBox()

		devices = get_audio_input_devices()
		self.device_combo.addItems(devices)

		current_device = settings.get("audio", "device")
		for i, dev in enumerate(devices):
			if current_device.lower() in dev.lower():
				self.device_combo.setCurrentIndex(i)
				break

		h1.addWidget(self.device_combo)
		layout.addLayout(h1)

		h_sample_rate = QHBoxLayout()
		h_sample_rate.addWidget(QLabel("Частота дискретизации:"))

		self.sample_rate_combo = QComboBox()
		sr_values = ["16000", "22050", "44100", "48000"]
		self.sample_rate_combo.addItems(sr_values)
		curr_sr = str(settings.get("audio", "sample_rate"))
		self.sample_rate_combo.setCurrentText(curr_sr)
		self.sample_rate_combo.setToolTip(
			"Указывает частоту дискретизации звука.\n\n"
			"Если не уверены, оставьте 22050."
		)

		h_sample_rate.addWidget(self.sample_rate_combo)
		layout.addLayout(h_sample_rate)

		h_block_size = QHBoxLayout()
		h_block_size.addWidget(QLabel("Размер блока"))

		self.bs_combo = QComboBox()
		bs_values = ["256", "512", "1024"]
		self.bs_combo.addItems(bs_values)
		curr_bs = str(settings.get("audio", "block_size"))
		self.bs_combo.setCurrentText(curr_bs)
		self.bs_combo.setToolTip(
			"Указывает размер блока аудио для обработки\n\n"
			"Если не уверены, оставьте 512"
		)

		h_block_size.addWidget(self.bs_combo)
		layout.addLayout(h_block_size)

		h2 = QHBoxLayout()
		h2.addWidget(QLabel("Порог тишины:"))
		self.threshold_spin = QDoubleSpinBox()
		self.threshold_spin.setRange(0.001, 0.5)
		self.threshold_spin.setSingleStep(0.005)
		self.threshold_spin.setDecimals(3)
		self.threshold_spin.setValue(settings.get("audio", "silence_threshold"))
		self.threshold_spin.setToolTip(
			"Порог громкости в нормализованных единицах.\n"
			"Это среднеквадратичное значение (RMS) амплитуды звука.\n"
			"0.0 - полная тишина, 1.0 - максимальная громкость.\n\n"
			"Если не уверены, используйте автокалибровку громкости."
		)
		h2.addWidget(self.threshold_spin)

		self.calibrate_btn = QPushButton("Авто")
		self.calibrate_btn.setToolTip(
			"Автоматически определить порог тишины.\n"
			"Программа прослушает 3 секунды тишины и\n"
			"установит порог на ее основе."
		)
		self.calibrate_btn.clicked.connect(self._calibrate)
		h2.addWidget(self.calibrate_btn)

		layout.addLayout(h2)

		h_cal = QHBoxLayout()
		h_cal.addWidget(QLabel("Коэффициэнт калибровки:"))
		self.cal_multiplier_spin = QDoubleSpinBox()
		self.cal_multiplier_spin.setRange(1.0, 5.0)
		self.cal_multiplier_spin.setSingleStep(0.1)
		self.cal_multiplier_spin.setDecimals(1)
		self.cal_multiplier_spin.setValue(settings.get("audio", "calibration_multiplier"))
		self.cal_multiplier_spin.setToolTip(
			"Множитель для автокалибровки.\n"
			"Порог = средний шум * коэффициент\n\n"
			"2.0 - порог в 2 раза выше шума (рекомендуется)\n"
			"3.0 - более агрессивная фильтрация\n\n"
			"Если не уверены, оставьте 2.0"
		)
		h_cal.addWidget(self.cal_multiplier_spin)
		layout.addLayout(h_cal)

		h3 = QHBoxLayout()
		h3.addWidget(QLabel("Гистерезис:"))
		self.hyst_spin = QDoubleSpinBox()
		self.hyst_spin.setRange(0.1, 1.0)
		self.hyst_spin.setSingleStep(0.05)
		self.hyst_spin.setDecimals(2)
		self.hyst_spin.setValue(settings.get("audio", "hysteresis"))
		self.hyst_spin.setToolTip(
			"Гистерезис предотвращает дерганье рта на посторонние шумы.\n"
			"Рот закрывается, когда громкость падает ниже\n"
			"Порог тишины * гистерезис\n\n"
			"Чем меньше значение, тем резче закрывается рот.\n\n"
			"Если не уверены, оставьте 0.7"
		)
		h3.addWidget(self.hyst_spin)
		layout.addLayout(h3)

		layout.addWidget(QLabel("<b>Аватар</b>"))

		h4 = QHBoxLayout()
		h4.addWidget(QLabel("Пакеты лиц:"))
		self.package_combo = QComboBox()

		# Загружаем список пакетов
		packages = list_available_packages(AVATARS_DIR)
		self.package_names = [pkg.path.name for pkg in packages]
		self.package_combo.addItems(self.package_names)

		# Выбираем текущий пакет
		current_package = settings.get("avatar", "package")
		if current_package in self.package_names:
			self.package_combo.setCurrentIndex(self.package_names.index(current_package))

		h4.addWidget(self.package_combo)
		layout.addLayout(h4)

		# --- Кнопки ---
		btn_layout = QHBoxLayout()
		btn_save = QPushButton("Сохранить")
		btn_cancel = QPushButton("Отмена")
		btn_save.clicked.connect(self.accept)
		btn_cancel.clicked.connect(self.reject)
		btn_layout.addStretch()
		btn_layout.addWidget(btn_save)
		btn_layout.addWidget(btn_cancel)
		layout.addLayout(btn_layout)

	def _calibrate(self):
		self.calibrate_btn.setEnabled(False)
		self.calibrate_btn.setText("Калибрую...")
		QApplication.processEvents()

		try:
			temp_thread = AudioThread(self.settings)
			new_threshold = temp_thread.calibrate(duration=3.0)

			self.threshold_spin.setValue(new_threshold)
			print(f"[AudioThread(Calibrate)] Новый порог: {new_threshold}")

		except Exception as e:
			print(f"[AudioThread(Calibrate)] Ошибка калибровки: {e}")
		finally:
			self.calibrate_btn.setEnabled(True)
			self.calibrate_btn.setText("Авто")

	def accept(self):
		# Сохраняем выбранное устройство
		selected_device = self.device_combo.currentText()
		self.settings.set("audio", "device", selected_device)

		# Сохраняем порог и гистерезис
		self.settings.set("audio", "sample_rate", int(self.sample_rate_combo.currentText()))
		self.settings.set("audio", "block_size", int(self.bs_combo.currentText()))
		self.settings.set("audio", "silence_threshold", self.threshold_spin.value())
		self.settings.set("audio", "hysteresis", self.hyst_spin.value())
		self.settings.set("audio", "calibration_multiplier", self.cal_multiplier_spin.value())

		# Сохраняем выбранный пакет лиц
		selected_package = self.package_combo.currentText()
		self.settings.set("avatar", "package", selected_package)

		self.settings.save()
		super().accept()


class AboutDialog(QDialog):
	"""Диалог 'О программе'"""

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle(f"О программе - {APP_NAME}")
		self.setMinimumSize(500, 400)

		layout = QVBoxLayout(self)

		tabs = QTabWidget()

		about_widget = QWidget()
		about_layout = QVBoxLayout(about_widget)

		about_label = QLabel()
		about_label.setWordWrap(True)
		about_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
		about_label.setTextFormat(Qt.RichText)
		about_label.setText(
			f"<h2>{APP_NAME}</h2>"
			f"<p><b>Версия:</b> {APP_VERSION}</p>"
			f"<p>{APP_DESCRIPTION}</p>"
			f"<p><b>Автор:</b> stas_unt</p>"
		)
		about_layout.addWidget(about_label)
		tabs.addTab(about_widget, "О программе")

		licenses_widget = QWidget()
		licenses_layout = QVBoxLayout(licenses_widget)

		licenses_text = QTextEdit()
		licenses_text.setReadOnly(True)
		licenses_text.setPlainText(
			"ImageTuber использует следующие библиотеки с открытым исходным кодом:\n\n"
			"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

			"PySide6 (Qt for Python)\n"
			"Лицензия: GNU Lesser General Public License v3.0 (LGPL-3.0)\n"
			"Copyright © 2026 The Qt Company Ltd.\n"
			"https://www.qt.io/\n\n"

			"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

			"soundcard\n"
            "Лицензия: MIT License\n"
            "Copyright © 2017 Bastian Bechtold\n"
            "https://github.com/bastibe/python-soundcard\n\n"

			"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

			"NumPy\n"
			"Лицензия: BSD 3-Clause License\n"
			"Copyright © 2005-2026 NumPy Developers\n"
			"https://numpy.org/\n\n"

			"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

			"tomli (для чтения TOML в Python < 3.11)\n"
			"Лицензия: MIT License\n"
			"Copyright © 2021 Taneli Hukkinen\n"
			"https://github.com/hukkin/tomli\n\n"

			"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

			"tomli-w (для записи TOML)\n"
			"Лицензия: MIT License\n"
			"Copyright © 2021 Taneli Hukkinen\n"
			"https://github.com/hukkin/tomli-w\n\n"

			"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

			"Полные тексты лицензий доступны по ссылкам выше или в репозиториях проектов."
		)
		licenses_layout.addWidget(licenses_text)
		tabs.addTab(licenses_widget, "Лицензии")

		layout.addWidget(tabs)

		button_box = QDialogButtonBox(QDialogButtonBox.Ok)
		button_box.accepted.connect(self.accept)
		layout.addWidget(button_box)

class ImageTuberApp:


	def __init__(self):
		signal.signal(signal.SIGINT, signal.SIG_DFL)

		self.app = QApplication(sys.argv)
		self.app.setQuitOnLastWindowClosed(False)

		if ICON_PATH.exists():
			self.app.setWindowIcon(QIcon(str(ICON_PATH)))

		self.timer = QTimer()
		self.timer.start(500)
		self.timer.timeout.connect(lambda: None)

		self.settings = Settings()
		self.audio_thread = None
		self.avatar_window = None

		self._setup_tray()
		self._start_avatar()

	def _setup_tray(self):
		self.tray = QSystemTrayIcon()

		if ICON_PATH.exists():
			self.tray.setIcon(QIcon(str(ICON_PATH)))
		else:
			icon_path = AVATARS_DIR / self.settings.get("avatar", "package") / "faces" / "normal" / "mouth_closed.png"
			icon = QIcon(QPixmap(icon_path))
			self.tray.setIcon(icon)

		self.tray.setToolTip(APP_NAME)
		self.tray.setVisible(True)

		# Меню
		menu = QMenu()

		action_settings = menu.addAction("Настройки")
		action_settings.triggered.connect(self._open_settings)

		action_about = menu.addAction("О программе")
		action_about.triggered.connect(self._show_about)

		menu.addSeparator()

		action_quit = menu.addAction("Выход")
		action_quit.triggered.connect(self._quit)

		self.tray.setContextMenu(menu)

	def _start_avatar(self):
		"""Запускаем окно аватара и аудио-поток."""
		self.avatar_window = AvatarWindow(self.settings)
		self.avatar_window.show()

		self.audio_thread = AudioThread(self.settings)
		self.audio_thread.speaking_changed.connect(self.avatar_window.set_speaking)
		print("[Main] Запуск потока аудио...")
		self.audio_thread.start()
		print(f"[Main] Аудио-поток запущен, isRunning={self.audio_thread.isRunning()}")

	def _restart_audio(self):
		"""Перезапуск аудио-потока после изменение настроек"""
		if self.audio_thread:
			self.audio_thread.stop()
			self.audio_thread.wait()
		self.audio_thread = AudioThread(self.settings)
		self.audio_thread.speaking_changed.connect(self.avatar_window.set_speaking)
		self.audio_thread.start()

	def _open_settings(self):
		dialog = SettingsDialog(self.settings)
		if dialog.exec():
			# После сохранения - перезапускаем аудио и рендер
			self._restart_audio()
			self.avatar_window.reload_package()

	def _show_about(self):
		dialog = AboutDialog()
		dialog.exec()

	def _quit(self):
		print(f"\n[Main] Завершение работы...")
		if self.audio_thread:
			self.audio_thread.stop()
			self.audio_thread.wait()
		if self.avatar_window:
			self.avatar_window.close()
		self.tray.setVisible(False)
		self.app.quit()

	def run(self):
		try:
			sys.exit(self.app.exec())
		except KeyboardInterrupt:
			self._quit()


def main():
	app = ImageTuberApp()
	app.run()


if __name__ == "__main__":
	main()
