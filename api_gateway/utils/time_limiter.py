import threading
import time
import logging
from typing import Callable, Any
import functools

logger = logging.getLogger(__name__)

class TimeoutException(Exception):
    """Exception được ném khi một function chạy quá thời gian quy định."""
    def __init__(self, timeout):
        self.timeout = timeout
        super().__init__(f"Function đã chạy quá thời gian giới hạn ({timeout} giây)")

def time_limit(function: Callable, seconds: int = 10) -> Any:
    """
    Thực hiện một function với giới hạn thời gian.
    
    Args:
        function: Function cần chạy
        seconds: Thời gian giới hạn (giây)
        
    Returns:
        Kết quả của function nếu nó hoàn thành trong thời gian quy định
        
    Raises:
        TimeoutException: Nếu function chạy quá thời gian quy định
    """
    result = None
    exception = None
    finished = False
    
    # Function sẽ chạy trong thread riêng
    def target():
        nonlocal result, exception, finished
        try:
            result = function()
        except Exception as e:
            exception = e
        finally:
            finished = True
    
    # Tạo và chạy thread
    thread = threading.Thread(target=target)
    thread.daemon = True  # Thread sẽ kết thúc khi main thread kết thúc
    
    start_time = time.time()
    thread.start()
    
    # Chờ thread hoàn thành hoặc hết thời gian
    thread.join(seconds)
    
    # Kiểm tra kết quả
    if not finished:
        elapsed = time.time() - start_time
        logger.warning(f"Function timeout after {elapsed:.2f} seconds (limit: {seconds}s)")
        raise TimeoutException(seconds)
    
    # Nếu có exception xảy ra trong thread, ném lại
    if exception is not None:
        raise exception
    
    return result

class TimeLimiter:
    """
    Class decorator để áp dụng giới hạn thời gian cho các method.
    """
    
    def __init__(self, seconds: int = 10):
        """
        Khởi tạo TimeLimiter.
        
        Args:
            seconds: Thời gian giới hạn (giây)
        """
        self.seconds = seconds
    
    def __call__(self, func: Callable) -> Callable:
        """
        Decorator để áp dụng giới hạn thời gian cho function.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return time_limit(lambda: func(*args, **kwargs), self.seconds)
        return wrapper
