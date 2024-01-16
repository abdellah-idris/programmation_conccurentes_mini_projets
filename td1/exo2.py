import threading


def find_solution(s, k, start, step, result_lock, result_holder, finish_event):
    n = start

    while not finish_event.is_set():
        hash_result = abs(hash((s, n))) % pow(10, k)

        if hash_result == 0:
            with result_lock:
                result_holder[0] = n
            finish_event.set()
            break

        n += step


def solve_puzzle(s, k):
    result_lock = threading.Lock()
    result_holder = [None]

    finish_event = threading.Event()

    # Create two threads, one for even values of n, and the other for odd values
    thread_even = threading.Thread(target=find_solution, args=(s, k, 0, 2, result_lock, result_holder, finish_event))
    thread_odd = threading.Thread(target=find_solution, args=(s, k, 1, 2, result_lock, result_holder, finish_event))

    # Start the threads
    thread_even.start()
    thread_odd.start()

    # Wait for either thread to finish
    thread_even.join()
    thread_odd.join()

    # Check which thread finished first
    if result_holder[0] is not None:
        print(f"Thread {thread_even.name if result_holder[0] % 2 == 0 else thread_odd.name} finished first.")
    else:
        print("No solution found.")

    return result_holder[0]


if __name__ == "__main__":
    s = "example_string"
    k = 5

    result = solve_puzzle(s, k)

    print(f"Found solution: {result}")
