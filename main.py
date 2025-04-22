import os
import sys
import threading
import time
import subprocess
import logging
import signal
from api_gateway.app import app

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_service(cmd, service_name):
    """Chạy một service và ghi log"""
    logger.info(f"Khởi động {service_name}...")
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    logger.info(f"Đã khởi động {service_name} (PID: {process.pid})")
    
    # Ghi log từ service
    if process.stdout:
        for line in process.stdout:
            logger.info(f"[{service_name}] {line.strip()}")
    
    # Kiểm tra khi service kết thúc
    exit_code = process.wait()
    logger.info(f"{service_name} đã kết thúc với exit code: {exit_code}")

def start_services():
    """Khởi động tất cả các service"""
    # Khởi động Payment Service
    payment_thread = threading.Thread(
        target=run_service,
        args=("python payment_service/app.py", "Payment Service"),
        daemon=True
    )
    payment_thread.start()
    
    # Khởi động Inventory Service
    inventory_thread = threading.Thread(
        target=run_service,
        args=("python inventory_service/app.py", "Inventory Service"),
        daemon=True
    )
    inventory_thread.start()
    
    # Khởi động Shipping Service
    shipping_thread = threading.Thread(
        target=run_service,
        args=("python shipping_service/app.py", "Shipping Service"),
        daemon=True
    )
    shipping_thread.start()
    
    # Đợi các service khởi động
    logger.info("Đợi các service khởi động...")
    time.sleep(5)
    logger.info("Tất cả các service đã khởi động")

# Khởi động các service nền
start_services()

# Tạo Flask app để Gunicorn có thể tìm thấy
# Gunicorn sẽ sử dụng biến app này
# Workflow sẽ chạy lệnh: `gunicorn --bind 0.0.0.0:5000 main:app`

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)