import os
import uuid
import logging
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from models import ShippingOrder, ShippingStatus, ShippingLocation, db

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shipping.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Khởi tạo database
db.init_app(app)

# Tạo bảng nếu chưa tồn tại
with app.app_context():
    db.create_all()

@app.route('/shipping', methods=['POST'])
def create_shipping():
    """Tạo một đơn vận chuyển mới"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Không có dữ liệu được gửi'}), 400
    
    required_fields = ['customer_id', 'address', 'items']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Thiếu trường dữ liệu: {field}'}), 400
    
    try:
        # Tạo một ID vận chuyển mới
        shipping_id = f"SHP-{uuid.uuid4().hex[:8].upper()}"
        
        # Tính toán thời gian giao hàng dự kiến (giả lập)
        # Thông thường, service sẽ tích hợp với nhà vận chuyển để có thời gian chính xác
        today = datetime.now()
        estimated_delivery = today + timedelta(days=3)  # 3 ngày sau
        
        # Tạo đơn vận chuyển mới
        shipping = ShippingOrder(
            id=shipping_id,
            customer_id=data['customer_id'],
            address=data['address'],
            items=json.dumps(data['items']),
            payment_id=data.get('payment_id', ''),
            estimated_delivery=estimated_delivery,
            status='processing'  # Trạng thái ban đầu: đang xử lý
        )
        
        # Lưu vào database
        db.session.add(shipping)
        # Commit để lưu shipping order trước
        db.session.commit()
        
        # Tạo trạng thái ban đầu
        initial_status = ShippingStatus(
            shipping_id=shipping_id,
            status='processing',
            description='Đơn hàng đang được xử lý'
        )
        db.session.add(initial_status)
        
        # Tạo vị trí ban đầu
        initial_location = ShippingLocation(
            shipping_id=shipping_id,
            location='Kho hàng trung tâm',
            latitude=10.823099,  # Giả sử kho hàng ở TP.HCM
            longitude=106.629662
        )
        db.session.add(initial_location)
        
        # Commit lần thứ hai để lưu các đối tượng liên quan
        db.session.commit()
        
        logger.info(f"Đã tạo đơn vận chuyển mới: {shipping_id}")
        
        return jsonify({
            'id': shipping.id,
            'customer_id': shipping.customer_id,
            'payment_id': shipping.payment_id,
            'status': shipping.status,
            'estimated_delivery': shipping.estimated_delivery.isoformat(),
            'created_at': shipping.created_at.isoformat()
        }), 201
        
    except Exception as e:
        logger.exception(f"Lỗi khi tạo đơn vận chuyển: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Lỗi khi tạo đơn vận chuyển: {str(e)}'}), 500

@app.route('/shipping/<shipping_id>', methods=['GET'])
def get_shipping(shipping_id):
    """Lấy thông tin chi tiết đơn vận chuyển"""
    try:
        shipping = ShippingOrder.query.get(shipping_id)
        
        if not shipping:
            return jsonify({'error': f'Không tìm thấy đơn vận chuyển với ID: {shipping_id}'}), 404
        
        # Lấy lịch sử trạng thái
        statuses = ShippingStatus.query.filter_by(shipping_id=shipping_id).order_by(ShippingStatus.created_at).all()
        status_history = [{
            'status': status.status,
            'description': status.description,
            'created_at': status.created_at.isoformat()
        } for status in statuses]
        
        # Lấy lịch sử vị trí
        locations = ShippingLocation.query.filter_by(shipping_id=shipping_id).order_by(ShippingLocation.created_at).all()
        location_history = [{
            'location': location.location,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'created_at': location.created_at.isoformat()
        } for location in locations]
        
        items = json.loads(shipping.items)
        
        result = {
            'id': shipping.id,
            'customer_id': shipping.customer_id,
            'address': shipping.address,
            'payment_id': shipping.payment_id,
            'items': items,
            'status': shipping.status,
            'estimated_delivery': shipping.estimated_delivery.isoformat(),
            'delivered_at': shipping.delivered_at.isoformat() if shipping.delivered_at else None,
            'created_at': shipping.created_at.isoformat(),
            'status_history': status_history,
            'location_history': location_history
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi lấy thông tin đơn vận chuyển: {str(e)}")
        return jsonify({'error': f'Lỗi khi lấy thông tin đơn vận chuyển: {str(e)}'}), 500

@app.route('/shipping/<shipping_id>/update', methods=['PUT'])
def update_shipping(shipping_id):
    """Cập nhật trạng thái đơn vận chuyển"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Không có dữ liệu được gửi'}), 400
    
    if 'status' not in data:
        return jsonify({'error': 'Thiếu trường dữ liệu: status'}), 400
    
    try:
        shipping = ShippingOrder.query.get(shipping_id)
        
        if not shipping:
            return jsonify({'error': f'Không tìm thấy đơn vận chuyển với ID: {shipping_id}'}), 404
        
        new_status = data['status']
        description = data.get('description', '')
        
        # Kiểm tra trạng thái hợp lệ
        valid_statuses = ['processing', 'shipped', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Trạng thái không hợp lệ. Phải là một trong: {", ".join(valid_statuses)}'}), 400
        
        # Không thể thay đổi nếu đã giao hàng hoặc đã hủy
        if shipping.status in ['delivered', 'cancelled']:
            return jsonify({'error': f'Không thể thay đổi trạng thái đơn hàng đã {shipping.status}'}), 400
        
        # Cập nhật trạng thái
        shipping.status = new_status
        
        # Cập nhật thời gian giao hàng nếu trạng thái là 'delivered'
        if new_status == 'delivered':
            shipping.delivered_at = datetime.now()
        
        # Tạo bản ghi trạng thái mới
        status_record = ShippingStatus(
            shipping_id=shipping_id,
            status=new_status,
            description=description
        )
        db.session.add(status_record)
        
        # Cập nhật vị trí nếu có
        if 'location' in data:
            location_record = ShippingLocation(
                shipping_id=shipping_id,
                location=data['location'],
                latitude=data.get('latitude', 0),
                longitude=data.get('longitude', 0)
            )
            db.session.add(location_record)
        
        db.session.commit()
        
        logger.info(f"Đã cập nhật trạng thái đơn vận chuyển {shipping_id} thành {new_status}")
        
        return jsonify({
            'id': shipping.id,
            'status': shipping.status,
            'updated_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi cập nhật trạng thái đơn vận chuyển: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Lỗi khi cập nhật trạng thái đơn vận chuyển: {str(e)}'}), 500

@app.route('/shipping', methods=['GET'])
def list_shipping():
    """Lấy danh sách các đơn vận chuyển"""
    try:
        customer_id = request.args.get('customer_id')
        status = request.args.get('status')
        
        # Tạo query
        query = ShippingOrder.query
        
        # Thêm filter nếu có
        if customer_id:
            query = query.filter_by(customer_id=customer_id)
        if status:
            query = query.filter_by(status=status)
        
        # Thực hiện query và lấy kết quả
        shipping_orders = query.order_by(ShippingOrder.created_at.desc()).all()
        
        result = [{
            'id': order.id,
            'customer_id': order.customer_id,
            'payment_id': order.payment_id,
            'status': order.status,
            'estimated_delivery': order.estimated_delivery.isoformat(),
            'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
            'created_at': order.created_at.isoformat()
        } for order in shipping_orders]
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi lấy danh sách đơn vận chuyển: {str(e)}")
        return jsonify({'error': f'Lỗi khi lấy danh sách đơn vận chuyển: {str(e)}'}), 500

@app.route('/tracking/<shipping_id>', methods=['GET'])
def track_shipping(shipping_id):
    """Theo dõi đơn vận chuyển (API công khai cho khách hàng)"""
    try:
        shipping = ShippingOrder.query.get(shipping_id)
        
        if not shipping:
            return jsonify({'error': f'Không tìm thấy đơn vận chuyển với ID: {shipping_id}'}), 404
        
        # Lấy lịch sử trạng thái
        statuses = ShippingStatus.query.filter_by(shipping_id=shipping_id).order_by(ShippingStatus.created_at).all()
        status_history = [{
            'status': status.status,
            'description': status.description,
            'created_at': status.created_at.isoformat()
        } for status in statuses]
        
        # Lấy vị trí hiện tại (mới nhất)
        current_location = ShippingLocation.query.filter_by(shipping_id=shipping_id).order_by(ShippingLocation.created_at.desc()).first()
        
        location_info = None
        if current_location:
            location_info = {
                'location': current_location.location,
                'latitude': current_location.latitude,
                'longitude': current_location.longitude,
                'updated_at': current_location.created_at.isoformat()
            }
        
        result = {
            'id': shipping.id,
            'status': shipping.status,
            'estimated_delivery': shipping.estimated_delivery.isoformat(),
            'delivered_at': shipping.delivered_at.isoformat() if shipping.delivered_at else None,
            'current_location': location_info,
            'status_history': status_history
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi theo dõi đơn vận chuyển: {str(e)}")
        return jsonify({'error': f'Lỗi khi theo dõi đơn vận chuyển: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Kiểm tra trạng thái dịch vụ"""
    return jsonify({
        'status': 'ok',
        'service': 'shipping',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003, debug=True)
