from multiprocessing import Process, Queue
import pyttsx3

def tts_worker(q):
    engine = pyttsx3.init()
    while True:
        text = q.get()  # Warte auf neuen Text
        if text == "STOP":
            break
        engine.say(text)
        engine.runAndWait()

class Voice:
    def __init__(self):
        self.queue = Queue()
        self.process = Process(target=tts_worker, args=(self.queue,))
        self.process.start()

    def say(self, text):
        self.queue.put(text)

    def stop(self):
        self.queue.put("STOP")
        self.process.terminate()
