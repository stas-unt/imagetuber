import numpy as np
import sounddevice as sd
from PySide6.QtCore import QThread, Signal

class AudioThread(QThread):
	speaking_changed = Signal(bool)

	def __init__(self, settings):
		super().__init__()
		self._running = True
		self.settings = settings
		self.device_name = settings.get("audio", "device")
		self.sample_rate = settings.get("audio", "sample_rate", 48000)
		self.block_size = settings.get("audio", "block_size", 1024)
		self.silence_threshold = settings.get("audio", "silence_threshold", 0.02)
		self.hysteresis = settings.get("audio", "hysteresis", 0.7)
		self.stream = None

	def _find_device(self):
		devices = sd.query_devices()
		for i, dev in enumerate(devices):
			if self.device_name.lower() in dev["name"].lower() and dev["max_input_channels"] > 0:
				return i
		return None

	def run(self):
		print(f"[AudioThread] started, device={self.device_name}")

		device = self._find_device()
		if device is None:
			print(f"[AudioThread] Устройство '{self.device_name}' не найдено"
					f"использую устройство по умолчанию")

		is_speaking = False

		threshold_open = self.silence_threshold
		threshold_closed = self.silence_threshold * self.hysteresis

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
			'samplerate': self.sample_rate,
			'channels': 1,
			'dtype': 'float32',
			'blocksize': self.block_size,
			'callback': callback
		}
		if device is not None:
			stream_kwargs['device'] = device

		try:
			self.stream = sd.InputStream(**stream_kwargs)
			self.stream.start()

			while self._running:
				QThread.msleep(50)
		except Exception as e:
			print(f"[AudioThread] Ошибка: {e}")
			return
		finally:
			if self.stream is not None:
				self.stream.stop()
				self.stream.close()

	def stop(self):
		self._running = False

def get_audio_input_devices() -> list[str]:
	"""Возвращает список названий всех устройств захвата звука"""
	devices = sd.query_devices()
	input_devices = []

	for dev in devices:
		if dev["max_input_channels"] > 0:
			input_devices.append(dev["name"])

	return input_devices
