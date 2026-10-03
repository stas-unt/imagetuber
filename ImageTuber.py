# ImageTuber
import sys
import signal
import numpy as np
import sounddevice as sd
from __future__ import annotations
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QMouseEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel

SAMPLE_RATE = 48000
BLOCK_SIZE = 1024
SILENCE_THRESHOLD = 0.05
HYSTERESIS = 0.7
IMG_OPEN = "./mouth_open.png"
IMG_CLOSED = "./mouth_closed.png"

class AudioThread(QThread):
	speaking_changed = Signal(bool)

	def __init__(self, device='Easy Effects Source'):
		super().__init__()
		self._running = True
		self.device = device
		self.stream = None

	def run(self):
		print(f"[AudioThread] started, device={self.device}")
		is_speaking = False

		threshold_open = SILENCE_THRESHOLD
		threshold_closed = SILENCE_THRESHOLD * HYSTERESIS

		def callback(indata, frames, time_info, status):
			nonlocal is_speaking
			if status:
				print("Audio status:", status)
			# indata - это numpy-массив семплов в диапазоне [-1, 1]
			rms = np.sqrt(np.mean(indata ** 2))

			if not is_speaking and rms > threshold_open:
				is_speaking = True
				self.speaking_changed.emit(True)
			elif is_speaking and rms < threshold_closed:
				is_speaking = False
				self.speaking_changed.emit(False)

		stream_kwargs = {
			'samplerate': SAMPLE_RATE,
			'channels': 1,
			'dtype': 'float32',
			'blocksize': BLOCK_SIZE,
			'callback': callback
		}
		if self.device is not None:
			stream_kwargs['device'] = self.device

		try:
			self.stream = sd.InputStream(**stream_kwargs)
			self.stream.start()

			while self._running:
				QThread.msleep(50)
		except Exception as e:
			print(f"Ошибка инициализации аудио: {e}")
			return
		finally:
			if self.stream is not None:
				self.stream.stop()
				self.stream.close()

	def stop(self):
		self._running = False

# ---- Окно с аватарами ----
class AvatarWindow(QWidget):
	def __init__(self):
		super().__init__()

		# Создаем прозрачное окно
		self.setWindowFlags(
			Qt.Window | Qt.FramelessWindowHint |
			Qt.WindowStaysOnTopHint | Qt.Tool
			)
		self.setAttribute(Qt.WA_TranslucentBackground)

		# Что-бы окно не кликалось
		self.setAttribute(Qt.WA_TransparentForMouseEvents)

		# Имя окна
		self.setWindowTitle("ImageTuber Camera (window)")

		self.label = QLabel(self)
		self.label.setScaledContents(True)

		self.pix_closed = QPixmap(IMG_CLOSED)
		self.pix_open= QPixmap(IMG_OPEN)

		if self.pix_closed.isNull() or self.pix_open.isNull():
			raise FileNotFoundError(
					"Не найдены картинки mouth_closed.png / mouth_open.png. "
					"Положи их в папку faces"
				)

		self.label.setPixmap(self.pix_closed)
		self.resize(self.pix_closed.size())

		screen = QApplication.primaryScreen().geometry()
		self.move(screen.width() - screen.width() - 50,
					screen.height() - screen.height() - 100)

	def set_speaking(self, speaking: bool):
		self.label.setPixmap(self.pix_open if speaking else self.pix_closed)

def main():
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	app = QApplication(sys.argv)

	timer = QTimer()
	timer.start(500)
	timer.timeout.connect(lambda: None)

	print("Доступные аудиоустройства:")
	print(sd.query_devices())
	print()

	device = 'Easy Effects Source'

	window = AvatarWindow()
	window.show()

	audio = AudioThread()
	print(f"[Main] Запуск потока аудио...")
	audio.speaking_changed.connect(window.set_speaking)
	audio.start()
	print(f"[Main] Поток аудио запущен, isRunning={audio.isRunning()}")

	try:
		sys.exit(app.exec())
	except KeyboardInterrupt:
		print("/nЗавершение работы...")
	finally:
		audio.stop()
		audio.wait()

# Init
if __name__ == '__main__':
	main()
