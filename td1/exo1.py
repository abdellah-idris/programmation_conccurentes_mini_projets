import threading
import numpy as np
import time

"""
we can see that the parallel execution time is much slower than the non-threaded execution time
"""
def matrix_multiply_element(i, j, A, B, result_matrix):
    N = A.shape[1]

    result = 0
    for k in range(N):
        result += A[i, k] * B[k, j]

    # Acquire the lock before writing to the shared result_matrix
    with lock:
        result_matrix[i, j] = result

def parallel_matrix_multiply(A, B):
    M = A.shape[0]
    P = B.shape[1]

    result_matrix = np.zeros((M, P))

    # Use a lock to synchronize access to the shared result_matrix
    global lock
    lock = threading.Lock()

    # Create threads
    threads = []
    for i in range(M):
        for j in range(P):
            thread = threading.Thread(target=matrix_multiply_element, args=(i, j, A, B, result_matrix))
            threads.append(thread)
            thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    return result_matrix

def non_threaded_matrix_multiply(A, B):
    M = A.shape[0]
    N = A.shape[1]
    P = B.shape[1]

    result_matrix = np.zeros((M, P))

    for i in range(M):
        for j in range(P):
            result = 0
            for k in range(N):
                result += A[i, k] * B[k, j]
            result_matrix[i, j] = result

    return result_matrix

if __name__ == "__main__":
    A = np.random.rand(100, 100)
    B = np.random.rand(100, 100)

    start_time = time.time()
    parallel_result = parallel_matrix_multiply(A, B)
    parallel_execution_time = time.time() - start_time

    start_time = time.time()
    non_threaded_result = non_threaded_matrix_multiply(A, B)
    non_threaded_execution_time = time.time() - start_time

    print("Matrix A shape:", A.shape)
    print("Matrix B shape:", B.shape)
    print("\nParallel Execution Time:", parallel_execution_time)
    print("Non-Threaded Execution Time:", non_threaded_execution_time)

    assert np.allclose(parallel_result, non_threaded_result), "Results do not match"
