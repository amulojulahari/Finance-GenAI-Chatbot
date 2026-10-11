import time


def timing(print_args=False):
    def decorator(method):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = method(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            try:
                if print_args:
                    print(f"Method '{method.__name__}' with args: {args} and kwargs: {kwargs} took {execution_time:.6f} seconds to execute.")
                else:
                    print(f"Method '{method.__name__}' took {execution_time:.6f} seconds to execute.")
            except Exception:
                print(f"Method '{method.__name__}' took {execution_time:.6f} seconds to execute")
            return result
        return wrapper
    return decorator
