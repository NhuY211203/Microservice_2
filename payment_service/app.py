import os
import uuid
import logging
import json
from datetime import datetime
from flask import Flask, jsonify, request
from models import PaymentTransaction, db

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Khởi tạo database
db.init_app(app)

# Tạo bảng nếu chưa tồn tại
with app.app_context():
    db.create_all()

@app.route('/payments', methods=['POST'])
def create_payment():
    """Tạo một giao dịch thanh toán mới"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Không có dữ liệu được gửi'}), 400
    
    required_fields = ['amount', 'payment_method']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Thiếu trường dữ liệu: {field}'}), 400
    
    try:
        # Tạo một ID giao dịch mới
        payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        
        # Tạo giao dịch thanh toán mới
        payment = PaymentTransaction(
            id=payment_id,
            amount=data['amount'],
            payment_method=data['payment_method'],
            customer_id=data.get('customer_id', 'GUEST'),
            status='pending'
        )
        
        # Lưu vào database
        db.session.add(payment)
        db.session.commit()
        
        # Xử lý thanh toán (giả lập)
        # Trong thực tế, đây là nơi tích hợp với các cổng thanh toán như PayPal, Stripe, v.v.
        if process_payment(payment):
            payment.status = 'completed'
            payment.completed_at = datetime.now()
            db.session.commit()
            logger.info(f"Thanh toán {payment_id} đã xử lý thành công")
        else:
            payment.status = 'failed'
            db.session.commit()
            logger.error(f"Thanh toán {payment_id} xử lý thất bại")
            return jsonify({
                'id': payment.id,
                'status': payment.status,
                'error': 'Không thể xử lý thanh toán'
            }), 400
        
        return jsonify({
            'id': payment.id,
            'amount': payment.amount,
            'status': payment.status,
            'payment_method': payment.payment_method,
            'customer_id': payment.customer_id,
            'created_at': payment.created_at.isoformat(),
            'completed_at': payment.completed_at.isoformat() if payment.completed_at else None
        }), 201
        
    except Exception as e:
        logger.exception(f"Lỗi khi xử lý thanh toán: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Lỗi khi xử lý thanh toán: {str(e)}'}), 500

@app.route('/payments/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    """Lấy thông tin giao dịch thanh toán"""
    try:
        payment = PaymentTransaction.query.get(payment_id)
        
        if not payment:
            return jsonify({'error': f'Không tìm thấy thanh toán với ID: {payment_id}'}), 404
        
        return jsonify({
            'id': payment.id,
            'amount': payment.amount,
            'status': payment.status,
            'payment_method': payment.payment_method,
            'customer_id': payment.customer_id,
            'created_at': payment.created_at.isoformat(),
            'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
            'refunded': payment.refunded,
            'refunded_at': payment.refunded_at.isoformat() if payment.refunded_at else None,
            'refund_reason': payment.refund_reason
        }), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi lấy thông tin thanh toán: {str(e)}")
        return jsonify({'error': f'Lỗi khi lấy thông tin thanh toán: {str(e)}'}), 500

@app.route('/payments/<payment_id>/refund', methods=['POST'])
def refund_payment(payment_id):
    """Hoàn tiền một giao dịch thanh toán"""
    try:
        payment = PaymentTransaction.query.get(payment_id)
        
        if not payment:
            return jsonify({'error': f'Không tìm thấy thanh toán với ID: {payment_id}'}), 404
        
        if payment.status != 'completed':
            return jsonify({'error': 'Chỉ có thể hoàn tiền cho các giao dịch đã hoàn thành'}), 400
        
        if payment.refunded:
            return jsonify({'error': 'Giao dịch này đã được hoàn tiền trước đó'}), 400
        
        data = request.json
        refund_reason = data.get('reason', 'Khách hàng yêu cầu hoàn tiền')
        
        # Xử lý hoàn tiền (giả lập)
        # Trong thực tế, đây là nơi tích hợp với các cổng thanh toán
        if process_refund(payment):
            payment.refunded = True
            payment.refunded_at = datetime.now()
            payment.refund_reason = refund_reason
            db.session.commit()
            logger.info(f"Đã hoàn tiền thanh toán {payment_id}")
        else:
            logger.error(f"Không thể hoàn tiền thanh toán {payment_id}")
            return jsonify({'error': 'Không thể xử lý yêu cầu hoàn tiền'}), 400
        
        return jsonify({
            'id': payment.id,
            'status': 'refunded',
            'refunded_at': payment.refunded_at.isoformat(),
            'refund_reason': payment.refund_reason
        }), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi hoàn tiền thanh toán: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Lỗi khi hoàn tiền thanh toán: {str(e)}'}), 500

@app.route('/payments', methods=['GET'])
def list_payments():
    """Lấy danh sách các giao dịch thanh toán"""
    try:
        customer_id = request.args.get('customer_id')
        status = request.args.get('status')
        
        # Tạo query
        query = PaymentTransaction.query
        
        # Thêm filter nếu có
        if customer_id:
            query = query.filter_by(customer_id=customer_id)
        if status:
            query = query.filter_by(status=status)
        
        # Thực hiện query và lấy kết quả
        payments = query.order_by(PaymentTransaction.created_at.desc()).all()
        
        result = [{
            'id': payment.id,
            'amount': payment.amount,
            'status': payment.status,
            'payment_method': payment.payment_method,
            'customer_id': payment.customer_id,
            'created_at': payment.created_at.isoformat(),
            'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
            'refunded': payment.refunded
        } for payment in payments]
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi lấy danh sách thanh toán: {str(e)}")
        return jsonify({'error': f'Lỗi khi lấy danh sách thanh toán: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Kiểm tra trạng thái dịch vụ"""
    return jsonify({
        'status': 'ok',
        'service': 'payment',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200

def process_payment(payment):
    """
    Xử lý giao dịch thanh toán (giả lập)
    Trong thực tế, đây là nơi tích hợp với các cổng thanh toán
    """
    logger.info(f"Đang xử lý thanh toán {payment.id} với phương thức {payment.payment_method}")
    
    # Giả lập thành công 90% số giao dịch
    import random
    return random.random() < 0.9

def process_refund(payment):
    """
    Xử lý hoàn tiền (giả lập)
    Trong thực tế, đây là nơi tích hợp với các cổng thanh toán
    """
    logger.info(f"Đang xử lý hoàn tiền cho thanh toán {payment.id}")
    
    # Giả lập thành công 95% số yêu cầu hoàn tiền
    import random
    return random.random() < 0.95

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)
