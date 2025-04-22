import logging
import time
import functools
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """
    Circuit Breaker pattern implementation.
    Giúp ngăn chặn các lỗi cascade khi một service bị lỗi bằng cách ngắt kết nối tạm thời
    và khôi phục sau một khoảng thời gian.
    """
    
    # Trạng thái của circuit breaker
    STATE_CLOSED = 'CLOSED'      # Bình thường, requests được xử lý
    STATE_OPEN = 'OPEN'          # Đang bị ngắt kết nối, không xử lý requests
    STATE_HALF_OPEN = 'HALF_OPEN'  # Thử nghiệm lại kết nối
    
    def __init__(self, 
                 failure_threshold: int = 5, 
                 recovery_timeout: int = 30, 
                 expected_exceptions: tuple = (Exception,)):
        """
        Khởi tạo Circuit Breaker.
        
        Args:
            failure_threshold: Số lần lỗi liên tiếp trước khi ngắt
            recovery_timeout: Thời gian (giây) trước khi thử kết nối lại
            expected_exceptions: Các loại exception được xem là lỗi
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        self.state = self.STATE_CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        
    def __call__(self, func: Callable) -> Any:
        """
        Decorator để bọc các function cần áp dụng Circuit Breaker.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Gọi function với Circuit Breaker pattern.
        """
        if self.state == self.STATE_OPEN:
            # Kiểm tra nếu đã đủ thời gian để reset
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                logger.info("Circuit Breaker chuyển sang trạng thái HALF-OPEN")
                self.state = self.STATE_HALF_OPEN
            else:
                logger.warning("Circuit Breaker đang OPEN, từ chối request")
                raise CircuitBreakerOpenException("Circuit Breaker đang mở, từ chối request")
        
        try:
            response = func(*args, **kwargs)
            
            # Nếu thành công và đang ở trạng thái half-open, đóng lại
            if self.state == self.STATE_HALF_OPEN:
                logger.info("Request thành công, Circuit Breaker đóng lại")
                self.state = self.STATE_CLOSED
                self.failure_count = 0
                
            # Reset failure count khi thành công
            self.failure_count = 0
            
            return response
            
        except self.expected_exceptions as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            # Nếu đã vượt quá ngưỡng lỗi, mở circuit breaker
            if self.failure_count >= self.failure_threshold:
                logger.error(f"Đã vượt quá ngưỡng lỗi {self.failure_threshold}, Circuit Breaker mở")
                self.state = self.STATE_OPEN
            
            # Ném lại exception
            raise e

class CircuitBreakerOpenException(Exception):
    """Exception khi Circuit Breaker đang trong trạng thái mở."""
    pass

# Singleton instance của Circuit Breaker
_circuit_breaker = CircuitBreaker()

def circuit_breaker(func: Callable) -> Any:
    """
    Decorator để áp dụng Circuit Breaker pattern cho function.
    Nếu truyền vào một lambda function, sẽ thực thi nó ngay lập tức.
    """
    if hasattr(func, '__name__') and func.__name__ == '<lambda>':
        # Đây là một lambda, thực thi ngay
        return _circuit_breaker.call(func)
    else:
        # Đây là một function thông thường, trả về decorator
        return _circuit_breaker(func)
