import threading

class Barrier:
    def __init__(self, n):
        self.n = n
        self.counter = 0
        self.condition = threading.Condition()

    def wait(self):
        with self.condition:
            self.counter += 1
            if self.counter == self.n:
                # All threads have reached the barrier, notify them
                self.condition.notify_all()
            else:
                # Wait for other threads to reach the barrier
                self.condition.wait()

if __name__ == "__main__":
    def thread_function(barrier):
        print("Thread started")
        # Simulate some work
        # ...

        # Wait for all threads to reach the barrier
        barrier.wait()

        print("Thread finished")

    # Create a barrier for 3 threads
    barrier = Barrier(3)

    # Create and start three threads
    thread1 = threading.Thread(target=thread_function, args=(barrier,))
    thread2 = threading.Thread(target=thread_function, args=(barrier,))
    thread3 = threading.Thread(target=thread_function, args=(barrier,))

    thread1.start()
    thread2.start()
    thread3.start()

    # Wait for all threads to finish
    thread1.join()
    thread2.join()
    thread3.join()
