import os
import logging
import json
import requests
from flask import Flask, jsonify, request, render_template
from utils.circuit_breaker import circuit_breaker
from utils.rate_limiter import rate_limit
from utils.retry import retry_request
from utils.time_limiter import time_limit

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Cấu hình các service URLs
SERVICE_URLS = {
    'payment': 'http://localhost:8001',
    'inventory': 'http://localhost:8002',
    'shipping': 'http://localhost:8003'
}

@app.route('/')
def index():
    """Trang chủ của API Gateway"""
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
@rate_limit(limit=10, period=60)  # Giới hạn 10 requests mỗi phút
def get_products():
    """Lấy danh sách sản phẩm từ Inventory Service"""
    try:
        @circuit_breaker
        def get_products_with_retry():
            return retry_request(
                lambda: time_limit(
                    lambda: requests.get(f"{SERVICE_URLS['inventory']}/products"),
                    seconds=5
                )
            )
        
        response = get_products_with_retry()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Lỗi khi lấy danh sách sản phẩm: {str(e)}")
        return jsonify({"error": "Không thể kết nối đến Inventory Service"}), 503

@app.route('/api/products/<product_id>', methods=['GET'])
@rate_limit(limit=20, period=60)
def get_product(product_id):
    """Lấy thông tin chi tiết sản phẩm từ Inventory Service"""
    try:
        response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.get(f"{SERVICE_URLS['inventory']}/products/{product_id}"),
                seconds=5
            )
        ))
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin sản phẩm {product_id}: {str(e)}")
        return jsonify({"error": "Không thể kết nối đến Inventory Service"}), 503

@app.route('/api/products', methods=['POST'])
@rate_limit(limit=5, period=60)
def create_product():
    """Tạo sản phẩm mới trong Inventory Service"""
    data = request.json
    try:
        response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.post(f"{SERVICE_URLS['inventory']}/products", json=data),
                seconds=5
            )
        ))
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Lỗi khi tạo sản phẩm mới: {str(e)}")
        return jsonify({"error": "Không thể kết nối đến Inventory Service"}), 503

@app.route('/api/inventory/update', methods=['POST'])
@rate_limit(limit=5, period=60)
def update_inventory():
    """Cập nhật tồn kho trong Inventory Service"""
    data = request.json
    try:
        response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.post(f"{SERVICE_URLS['inventory']}/update", json=data),
                seconds=5
            )
        ))
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật tồn kho: {str(e)}")
        return jsonify({"error": "Không thể kết nối đến Inventory Service"}), 503

@app.route('/api/payments', methods=['POST'])
@rate_limit(limit=5, period=60)
def create_payment():
    """Tạo thanh toán mới trong Payment Service"""
    data = request.json
    try:
        response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.post(f"{SERVICE_URLS['payment']}/payments", json=data),
                seconds=5
            )
        ))
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Lỗi khi tạo thanh toán: {str(e)}")
        return jsonify({"error": "Không thể kết nối đến Payment Service"}), 503

@app.route('/api/payments/<payment_id>', methods=['GET'])
@rate_limit(limit=10, period=60)
def get_payment(payment_id):
    """Lấy thông tin thanh toán từ Payment Service"""
    try:
        response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.get(f"{SERVICE_URLS['payment']}/payments/{payment_id}"),
                seconds=5
            )
        ))
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin thanh toán {payment_id}: {str(e)}")
        return jsonify({"error": "Không thể kết nối đến Payment Service"}), 503

@app.route('/api/payments/<payment_id>/refund', methods=['POST'])
@rate_limit(limit=3, period=60)
def refund_payment(payment_id):
    """Hoàn tiền thanh toán trong Payment Service"""
    data = request.json
    try:
        response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.post(f"{SERVICE_URLS['payment']}/payments/{payment_id}/refund", json=data),
                seconds=5
            )
        ))
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Lỗi khi hoàn tiền thanh toán {payment_id}: {str(e)}")
        return jsonify({"error": "Không thể kết nối đến Payment Service"}), 503

@app.route('/api/shipping', methods=['POST'])
@rate_limit(limit=5, period=60)
def create_shipping():
    """Tạo vận chuyển mới trong Shipping Service"""
    data = request.json
    try:
        response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.post(f"{SERVICE_URLS['shipping']}/shipping", json=data),
                seconds=5
            )
        ))
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Lỗi khi tạo vận chuyển: {str(e)}")
        return jsonify({"error": "Không thể kết nối đến Shipping Service"}), 503

@app.route('/api/shipping/<shipping_id>', methods=['GET'])
@rate_limit(limit=10, period=60)
def get_shipping(shipping_id):
    """Lấy thông tin vận chuyển từ Shipping Service"""
    try:
        response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.get(f"{SERVICE_URLS['shipping']}/shipping/{shipping_id}"),
                seconds=5
            )
        ))
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin vận chuyển {shipping_id}: {str(e)}")
        return jsonify({"error": "Không thể kết nối đến Shipping Service"}), 503

@app.route('/api/shipping/<shipping_id>/update', methods=['PUT'])
@rate_limit(limit=5, period=60)
def update_shipping(shipping_id):
    """Cập nhật trạng thái vận chuyển trong Shipping Service"""
    data = request.json
    try:
        response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.put(f"{SERVICE_URLS['shipping']}/shipping/{shipping_id}/update", json=data),
                seconds=5
            )
        ))
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật trạng thái vận chuyển {shipping_id}: {str(e)}")
        return jsonify({"error": "Không thể kết nối đến Shipping Service"}), 503

@app.route('/api/orders', methods=['POST'])
@rate_limit(limit=5, period=60)
def create_order():
    """Tạo đơn hàng mới (kết hợp thanh toán, cập nhật tồn kho và vận chuyển)"""
    data = request.json
    
    # 1. Kiểm tra và cập nhật tồn kho
    try:
        inventory_response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.post(f"{SERVICE_URLS['inventory']}/check", json=data['items']),
                seconds=5
            )
        ))
        
        if inventory_response.status_code != 200:
            return jsonify(inventory_response.json()), inventory_response.status_code
        
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra tồn kho: {str(e)}")
        return jsonify({"error": "Không thể kết nối đến Inventory Service"}), 503
    
    # 2. Tạo thanh toán
    try:
        payment_data = {
            "amount": data['total_amount'],
            "payment_method": data['payment_method'],
            "customer_id": data['customer_id']
        }
        
        payment_response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.post(f"{SERVICE_URLS['payment']}/payments", json=payment_data),
                seconds=5
            )
        ))
        
        if payment_response.status_code != 201:
            return jsonify(payment_response.json()), payment_response.status_code
        
        payment_info = payment_response.json()
        
    except Exception as e:
        logger.error(f"Lỗi khi tạo thanh toán: {str(e)}")
        return jsonify({"error": "Không thể kết nối đến Payment Service"}), 503
    
    # 3. Cập nhật tồn kho
    try:
        update_response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.post(f"{SERVICE_URLS['inventory']}/update", json=data['items']),
                seconds=5
            )
        ))
        
        if update_response.status_code != 200:
            # Hoàn tiền nếu cập nhật tồn kho thất bại
            refund_data = {"reason": "Cập nhật tồn kho thất bại"}
            requests.post(f"{SERVICE_URLS['payment']}/payments/{payment_info['id']}/refund", json=refund_data)
            return jsonify(update_response.json()), update_response.status_code
        
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật tồn kho: {str(e)}")
        # Hoàn tiền nếu cập nhật tồn kho thất bại
        refund_data = {"reason": "Cập nhật tồn kho thất bại"}
        requests.post(f"{SERVICE_URLS['payment']}/payments/{payment_info['id']}/refund", json=refund_data)
        return jsonify({"error": "Không thể kết nối đến Inventory Service"}), 503
    
    # 4. Tạo vận chuyển
    try:
        shipping_data = {
            "customer_id": data['customer_id'],
            "address": data['shipping_address'],
            "items": data['items'],
            "payment_id": payment_info['id']
        }
        
        shipping_response = circuit_breaker(lambda: retry_request(
            lambda: time_limit(
                lambda: requests.post(f"{SERVICE_URLS['shipping']}/shipping", json=shipping_data),
                seconds=5
            )
        ))
        
        if shipping_response.status_code != 201:
            # Hoàn tiền nếu tạo vận chuyển thất bại
            refund_data = {"reason": "Tạo vận chuyển thất bại"}
            requests.post(f"{SERVICE_URLS['payment']}/payments/{payment_info['id']}/refund", json=refund_data)
            return jsonify(shipping_response.json()), shipping_response.status_code
        
        shipping_info = shipping_response.json()
        
    except Exception as e:
        logger.error(f"Lỗi khi tạo vận chuyển: {str(e)}")
        # Hoàn tiền nếu tạo vận chuyển thất bại
        refund_data = {"reason": "Tạo vận chuyển thất bại"}
        requests.post(f"{SERVICE_URLS['payment']}/payments/{payment_info['id']}/refund", json=refund_data)
        return jsonify({"error": "Không thể kết nối đến Shipping Service"}), 503
    
    # 5. Trả về kết quả
    result = {
        "order_id": str(hash(f"{payment_info['id']}_{shipping_info['id']}_{data['customer_id']}")),
        "payment": payment_info,
        "shipping": shipping_info,
        "status": "Đơn hàng đã được tạo thành công"
    }
    
    return jsonify(result), 201

@app.route('/health', methods=['GET'])
def health_check():
    """Kiểm tra trạng thái các service"""
    health_status = {}
    
    for service, url in SERVICE_URLS.items():
        try:
            response = requests.get(f"{url}/health", timeout=2)
            health_status[service] = {
                "status": "up" if response.status_code == 200 else "down",
                "details": response.json() if response.status_code == 200 else {}
            }
        except:
            health_status[service] = {
                "status": "down",
                "details": {}
            }
    
    return jsonify({
        "gateway": "up",
        "services": health_status
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
