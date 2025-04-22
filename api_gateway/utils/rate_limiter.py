import time
import functools
from typing import Callable, Dict, List, Any
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate Limiter để giới hạn số lượng request trong một khoảng thời gian.
    Sử dụng thuật toán Sliding Window để theo dõi và giới hạn số lượng request.
    """
    
    def __init__(self):
        # Dictionary lưu trữ request history cho mỗi client
        # Key: IP address hoặc client identifier
        # Value: List of timestamps
        self.request_records: Dict[str, List[float]] = {}
    
    def is_allowed(self, client_id: str, limit: int, period: int) -> bool:
        """
        Kiểm tra xem client có bị giới hạn hay không.
        
        Args:
            client_id: Định danh của client (thường là IP)
            limit: Số lượng request tối đa được phép trong period
            period: Khoảng thời gian (giây) để tính giới hạn
            
        Returns:
            bool: True nếu request được phép, False nếu bị giới hạn
        """
        # Lấy thời gian hiện tại
        current_time = time.time()
        
        # Khởi tạo history cho client nếu chưa có
        if client_id not in self.request_records:
            self.request_records[client_id] = []
        
        # Lọc bỏ các timestamp cũ (ngoài period)
        self.request_records[client_id] = [
            timestamp for timestamp in self.request_records[client_id]
            if current_time - timestamp < period
        ]
        
        # Kiểm tra giới hạn
        if len(self.request_records[client_id]) >= limit:
            logger.warning(f"Rate limit exceeded for client {client_id}: {len(self.request_records[client_id])} requests in {period} seconds")
            return False
        
        # Thêm timestamp mới
        self.request_records[client_id].append(current_time)
        return True

# Singleton instance của RateLimiter
_rate_limiter = RateLimiter()

def rate_limit(limit: int = 10, period: int = 60):
    """
    Decorator để áp dụng rate limiting cho API endpoints.
    
    Args:
        limit: Số lượng request tối đa được phép trong period
        period: Khoảng thời gian (giây) để tính giới hạn
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Lấy định danh của client (ở đây dùng IP)
            client_id = request.remote_addr
            
            # Kiểm tra giới hạn
            if not _rate_limiter.is_allowed(client_id, limit, period):
                logger.warning(f"Rate limit exceeded for {request.path} from {client_id}")
                response = {
                    "error": "Đã vượt quá giới hạn request. Vui lòng thử lại sau.",
                    "limit": limit,
                    "period": period
                }
                return jsonify(response), 429  # 429 Too Many Requests
            
            # Cho phép request nếu chưa vượt quá giới hạn
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
