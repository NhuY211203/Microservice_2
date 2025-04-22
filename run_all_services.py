import subprocess
import threading
import time
import os
import signal
import sys

def run_service(command, service_name):
    """Chạy một service và xuất log ra màn hình"""
    print(f"Bắt đầu {service_name}...")
    
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        shell=True
    )
    
    print(f"Đã bắt đầu {service_name} (PID: {process.pid})")
    
    # Tạo một thread để đọc và hiển thị output
    def log_output():
        if process.stdout:  # Kiểm tra để tránh lỗi NoneType
            for line in process.stdout:
                print(f"[{service_name}] {line.strip()}")
    
    log_thread = threading.Thread(target=log_output)
    log_thread.daemon = True
    log_thread.start()
    
    return process

def main():
    """Chạy tất cả các service"""
    print("Khởi động hệ thống quản lý bán hàng microservices...")
    
    # Danh sách các process đang chạy
    processes = []
    
    try:
        # Bắt đầu API Gateway
        api_gateway_thread = threading.Thread(
            target=lambda: processes.append(run_service("python api_gateway/app.py", "API Gateway"))
        )
        api_gateway_thread.daemon = True
        api_gateway_thread.start()
        
        # Đợi một chút để API Gateway khởi động
        time.sleep(2)
        
        # Bắt đầu Payment Service
        payment_thread = threading.Thread(
            target=lambda: processes.append(run_service("python payment_service/app.py", "Payment Service"))
        )
        payment_thread.daemon = True
        payment_thread.start()
        
        # Bắt đầu Inventory Service
        inventory_thread = threading.Thread(
            target=lambda: processes.append(run_service("python inventory_service/app.py", "Inventory Service"))
        )
        inventory_thread.daemon = True
        inventory_thread.start()
        
        # Bắt đầu Shipping Service
        shipping_thread = threading.Thread(
            target=lambda: processes.append(run_service("python shipping_service/app.py", "Shipping Service"))
        )
        shipping_thread.daemon = True
        shipping_thread.start()
        
        print("Tất cả các service đã khởi động. Truy cập API Gateway tại http://localhost:5000")
        print("Nhấn Ctrl+C để dừng tất cả các service.")
        
        # Giữ chương trình chạy cho đến khi người dùng nhấn Ctrl+C
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nĐang dừng tất cả các service...")
        
        # Dừng tất cả các process
        for process in processes:
            if process and process.poll() is None:  # Nếu process vẫn đang chạy
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    process.kill()
        
        print("Đã dừng tất cả các service.")
        
if __name__ == "__main__":
    main()