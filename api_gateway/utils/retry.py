import time
import logging
import functools
from typing import Callable, Any, Optional, List, Union

logger = logging.getLogger(__name__)

def retry_request(
    func: Callable,
    retries: int = 3,
    delay: float = 0.5,
    backoff: float = 2,
    exceptions: Union[List[Exception], tuple] = (Exception,)
) -> Any:
    """
    Thực hiện lại request với cơ chế exponential backoff khi gặp lỗi.
    
    Args:
        func: Function cần thực hiện lại
        retries: Số lần thử lại tối đa
        delay: Thời gian chờ ban đầu giữa các lần thử (giây)
        backoff: Hệ số nhân thời gian chờ sau mỗi lần thử
        exceptions: Các loại exception cần xử lý và thử lại
    
    Returns:
        Kết quả của function nếu thành công
        
    Raises:
        Exception: Nếu đã thử lại hết số lần mà vẫn không thành công
    """
    max_retries = retries
    current_delay = delay
    last_exception = None
    
    # Thử request
    for retry in range(max_retries + 1):  # +1 để tính cả lần đầu tiên
        try:
            if retry > 0:
                logger.info(f"Retry attempt {retry}/{max_retries} after {current_delay:.2f}s delay")
            
            return func()
            
        except exceptions as e:
            logger.warning(f"Request failed (attempt {retry + 1}/{max_retries + 1}): {str(e)}")
            last_exception = e
            
            # Nếu đã hết số lần thử, ném exception
            if retry >= max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded for request")
                raise last_exception
            
            # Chờ trước khi thử lại
            time.sleep(current_delay)
            
            # Tăng thời gian chờ cho lần thử tiếp theo (exponential backoff)
            current_delay *= backoff
