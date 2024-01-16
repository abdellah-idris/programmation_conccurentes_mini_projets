import threading

def find_solution(s, k, start, step, result_lock, result_holder, finish_event):
    n = start

    while not finish_event.is_set():
        hash_result = abs(hash((s, n))) % pow(10, k)

        if hash_result == 0:
            with result_lock:
                result_holder[0] = n
            finish_event.set()  # Signal the other thread to stop
            break

        n += step

def solve_puzzle_for_list(strings, k):
    for s in strings:
        result_lock = threading.Lock()
        result_holder = [None]

        # Use an event to signal the threads to stop
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
            print(f"For string '{s}', Thread {thread_even.name if result_holder[0] % 2 == 0 else thread_odd.name} finished first. with n = {result_holder[0]}")
        else:
            print(f"For string '{s}', No solution found.")

if __name__ == "__main__":
    strings = ["example_string_1", "example_string_2", "example_string_3", "","example_string_4", "example_string_5"]
    k = 2

    solve_puzzle_for_list(strings, k)
