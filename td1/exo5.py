import threading
import time


class BarriereReutilisable:
    def __init__(self, nombre_threads):
        self.nombre_threads = nombre_threads
        self.compteur = 0
        self.mutex = threading.Lock()
        self.barriere = threading.Condition(self.mutex)

    def attendre(self):
        time.sleep(0.1)
        with self.mutex:
            self.compteur += 1
            if self.compteur < self.nombre_threads:
                self.barriere.wait()
            else:
                self.compteur = 0
                self.barriere.notify_all()

def fonction_thread(barriere):
    for i in range(3):
        print(f"Thread {threading.current_thread().name}, iteration {i} waiting")
        barriere.attendre()
        time.sleep(0.1)
        print(f"Thread {threading.current_thread().name}, iteration {i} passed \n")


nombre_threads = 3
barriere = BarriereReutilisable(nombre_threads)

threads = []
for i in range(nombre_threads):
    thread = threading.Thread(target=fonction_thread, args=(barriere,), name=f'Thread-{i}')
    threads.append(thread)

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

time.sleep(1)

print("Réutilisation")
threads = []
for i in range(nombre_threads):
    thread = threading.Thread(target=fonction_thread, args=(barriere,), name=f'Thread-{i}')
    threads.append(thread)

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()