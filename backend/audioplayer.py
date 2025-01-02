import subprocess
import threading
import time
from loguru import logger
import ffmpeg
import sounddevice as sd
import soundfile as sf
import multiprocessing
import queue
import numpy as np


class AudioPlayer:

    def __init__(self):
        self._process = None
        self._volume = multiprocessing.Value('d', 0.5)  #Value als gemeinsamer Speicher für Prozesse, um Lautstärke eines laufenden Streams ändern zu können
        self._q = None
        self._producer_running = False

    def play_file(self, file):
        """
        Spielt eine lokale Audiodatei ab.
        """
        try:
            # Daten lesen und Wiedergabe initialisieren
            data, samplerate = sf.read(file, dtype='float32')
            sd.default.reset()  # Optional: Zurücksetzen auf Standardgerät (falls nötig)
            logger.debug(f"Spiele Datei: {file} mit Lautstärke {self._volume.value:.2f}")

            # Wiedergabe starten
            with sd.OutputStream(samplerate=samplerate, channels=data.shape[1] if len(data.shape) > 1 else 1) as stream:
                block_size = 1024  # Blockweise Verarbeitung der Daten
                for i in range(0, len(data), block_size):
                    stream.write(data[i:i + block_size] * self._volume.value)

            logger.info(f"Datei {file} erfolgreich abgespielt.")
        except Exception as e:
            logger.error(f"Fehler bei der Datei-Wiedergabe: {e}")


    def play_stream(self, source):
        self.set_volume(self.get_volume())
        if self._process:
            self.stop()

        # Starte Thread für den Stream
        stream_thread = threading.Thread(target=self._start_stream, args=(source,))
        stream_thread.start()

    def _start_stream(self, source):
        """
        Führt das eigentliche Streaming aus.
        """
        if self._q is not None:
            self._clear_queue()
            logger.debug("Queue vollständig geleert.")

        # Füge eine kurze Pause ein, um sicherzustellen, dass der alte Stream beendet ist
        time.sleep(0.1)
        self._q = queue.Queue(maxsize=100)

        # FFmpeg-Prozess vorbereiten
        try:
            info = ffmpeg.probe(source)
        except ffmpeg.Error as e:
            logger.error(f"Fehler beim Analysieren des Streams: {e}")
            return

        streams = info.get('streams', [])
        if len(streams) != 1 or streams[0].get('codec_type') != 'audio':
            logger.error("Stream muss genau einen Audio-Stream enthalten.")
            return

        channels = streams[0]['channels']
        samplerate = float(streams[0]['sample_rate'])
        logger.debug(f"Stream-Kanäle: {channels}, Sample-Rate: {samplerate}")

        # Optimiertes FFmpeg-Kommando
        ffmpeg_command = (
            ffmpeg.input(source)
            .output('pipe:', format='f32le', acodec='pcm_f32le', ac=channels, ar=samplerate, loglevel='quiet')
            .compile()
        )

        try:
            process = subprocess.Popen(
                ffmpeg_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as e:
            logger.error(f"Fehler beim Starten von FFmpeg: {e}")
            return
        self._process = process
        self._producer_running = True

        # Producer-Thread zur Verarbeitung von FFmpeg-Ausgabe
        def producer_thread():
            try:
                read_size = 1024 * channels
                while self._producer_running:
                    raw_data = process.stdout.read(read_size * 4)
                    if len(raw_data) % (channels * 4) != 0:
                        logger.warning("Unvollständige Daten im Stream, ignoriere fehlerhafte Blöcke.")
                        continue
                    data = np.frombuffer(raw_data, dtype='float32').reshape(-1, channels)
                    self._q.put(data, timeout=0.1)
            except Exception as e:
                logger.error(f"Fehler im Producer-Thread: {e}")
            finally:
                self._producer_running = False
                process.terminate()
                process.wait()

        producer = threading.Thread(target=producer_thread)
        producer.daemon = True
        producer.start()

        # Sounddevice-Stream
        try:
            stream = sd.OutputStream(
                samplerate=samplerate,
                blocksize=1024,
                device=sd.default.device['output'],
                channels=channels,
                dtype='float32',
                callback=self._audio_callback,
            )
            with stream:
                while self._producer_running:
                    time.sleep(0.05)
        except Exception as e:
            logger.error(f"Fehler bei der Wiedergabe des Streams: {e}")
        finally:
            self._producer_running = False
            if self._process:
                self._process.terminate()
                self._process = None
            self._clear_queue()


    def _clear_queue(self):
        """Leert die Queue, um alte Datenreste zu entfernen."""
        if self._q is not None:
            while not self._q.empty():
                try:
                    self._q.get_nowait()
                except queue.Empty:
                    break

    def _audio_callback(self, outdata, frames, time, status):
        if status.output_underflow:
            raise sd.CallbackAbort
        try:
            data = self._q.get_nowait()
            # Dynamische Anwendung der Lautstärke
            with self._volume.get_lock():
                adjusted_volume = self._volume.value
            outdata[:] = data * adjusted_volume
        except queue.Empty:
            outdata.fill(0)  # Falls keine Daten verfügbar sind, fülle mit Stille



    def stop(self):
        logger.debug("Stop() wurde aufgerufen.")
        if self._producer_running:
            self._producer_running = False
            logger.debug("Producer-Thread wird beendet.")
        if self._process:
            logger.debug("FFmpeg-Prozess wird beendet.")
            self._process.terminate()
            self._process.wait()  # Warte auf die vollständige Beendigung
        if self._q is not None:
            self._clear_queue()  # Leere die Queue vollständig
        logger.debug("Wiedergabe vollständig gestoppt.")

    def is_playing(self):
        if self._process:
            return self._process.is_alive()

    def set_volume(self, volume):
        with self._volume.get_lock():  # Sperrt den Zugriff für andere Prozesse
            self._volume.value = max(0.0, min(volume, 1.0))

    def get_volume(self):
        with self._volume.get_lock():
            return self._volume.value

