import numpy as np
import soundcard as sc
import pdb
from PySide6.QtCore import QThread, Signal

class AudioThread(QThread):
	speaking_changed = Signal(bool)
	calibration_done = Signal(float)

	def __init__(self, settings):
		super().__init__()
		self._running = True
		self.settings = settings
		self.device_name = settings.get("audio", "device")
		self.sample_rate = settings.get("audio", "sample_rate", 48000)
		self.block_size = settings.get("audio", "block_size", 1024)
		self.silence_threshold = settings.get("audio", "silence_threshold", 0.02)
		self.hysteresis = settings.get("audio", "hysteresis", 0.7)
		self.calibration_multiplier = settings.get("audio", "calibration_multiplyer", 2.0)
		self.mic = None

	def _find_mic(self):
		all_mics = sc.all_microphones(include_loopback=True)

		for m in all_mics:
			if self.device_name.lower() in m.name.lower():
				return m

		print(f"[AudioThread] Устройство '{self.device_name}' не найдено, "
				f"используем микрофон по-умолчанию")
		return sc.default_microphone()

	def calibrate(self, duration: float = 3.0) -> float:
		print(f"[AudioThread] Калибровка, слушаю {duration} секунд тишины...")

		mic = self._find_mic()
		print(f"[AudioThread] Используем устройство {mic.name}")

		rms_values = []
		num_blocks = int(duration * self.sample_rate / self.block_size)

		stream = None

		try:
			with mic.recorder(samplerate=self.sample_rate, channels=1, blocksize=self.block_size) as rec:
				for i in range (num_blocks):
					data = rec.record(numframes=self.block_size)
				rms = np.sqrt(np.mean(data ** 2))
				rms_values.append(rms)
				print(f"[AudioThread] Калибровка: блок {i+1}/{num_blocks}, RMS={rms:.4f}")
		except Exception as e:
			print(f"[AudioThread] Ошибка калибровки: {e}")
			if not rms_values:
				return self.silence_threshold

		if not rms_values:
			return self.silence_threshold

		avg_noise = float(np.median(rms_values))
		new_threshold = avg_noise * self.calibration_multiplier

		print(f"[AudioThread] Средний уровень шума: {avg_noise:.4f}")
		print(f"[AudioThread] Новый порог: {new_threshold:.4f} "
				f"(шум * {self.calibration_multiplier})")

		return new_threshold

	def run(self):
		print(f"[AudioThread] started, device={self.device_name}")

		self.mic = self._find_mic()
		print(f"[AudioThread] Используется устройство '{self.mic.name}' как источник звука")

		is_speaking = False

		threshold_open = self.silence_threshold
		threshold_closed = self.silence_threshold * self.hysteresis

		try:
			with self.mic.recorder(samplerate=self.sample_rate, channels=1, blocksize=self.block_size) as rec:
				while self._running:
					data = rec.record(numframes=self.block_size)
					rms = np.sqrt(np.mean(data ** 2))

					if not is_speaking and rms > threshold_open:
						is_speaking = True
						self.speaking_changed.emit(True)
					elif is_speaking and rms < threshold_closed:
						is_speaking = False
						self.speaking_changed.emit(False)
		except Exception as e:
			print(f"[AudioThread] Ошибка: {e}")

	def stop(self):
		self._running = False

def get_audio_input_devices() -> list[str]:
	"""Возвращает список названий всех устройств захвата звука"""
	all_mics = sc.all_microphones(include_loopback=True)
	return [m.name for m in all_mics]
