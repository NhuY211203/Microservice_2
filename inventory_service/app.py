import os
import uuid
import logging
import json
from datetime import datetime
from flask import Flask, jsonify, request
from models import Product, InventoryTransaction, db

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Khởi tạo database
db.init_app(app)

# Tạo bảng nếu chưa tồn tại
with app.app_context():
    db.create_all()
    
    # Thêm dữ liệu mẫu nếu bảng sản phẩm trống
    if Product.query.count() == 0:
        sample_products = [
            Product(name="Laptop Dell XPS 13", price=25000000, stock=10, description="Laptop cao cấp với màn hình 13 inch"),
            Product(name="iPhone 13 Pro", price=28000000, stock=15, description="Điện thoại thông minh cao cấp từ Apple"),
            Product(name="Samsung Galaxy S21", price=20000000, stock=20, description="Điện thoại Android cao cấp từ Samsung"),
            Product(name="Tai nghe AirPods Pro", price=5000000, stock=25, description="Tai nghe không dây với khả năng chống ồn"),
            Product(name="Apple Watch Series 7", price=10000000, stock=12, description="Đồng hồ thông minh từ Apple")
        ]
        
        for product in sample_products:
            db.session.add(product)
        
        db.session.commit()

@app.route('/products', methods=['GET'])
def get_products():
    """Lấy danh sách tất cả sản phẩm"""
    try:
        products = Product.query.all()
        result = [{
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock,
            'description': product.description,
            'created_at': product.created_at.isoformat()
        } for product in products]
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi lấy danh sách sản phẩm: {str(e)}")
        return jsonify({'error': f'Lỗi khi lấy danh sách sản phẩm: {str(e)}'}), 500

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Lấy thông tin chi tiết một sản phẩm"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': f'Không tìm thấy sản phẩm với ID: {product_id}'}), 404
        
        result = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock,
            'description': product.description,
            'created_at': product.created_at.isoformat()
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi lấy thông tin sản phẩm {product_id}: {str(e)}")
        return jsonify({'error': f'Lỗi khi lấy thông tin sản phẩm: {str(e)}'}), 500

@app.route('/products', methods=['POST'])
def create_product():
    """Tạo sản phẩm mới"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Không có dữ liệu được gửi'}), 400
    
    required_fields = ['name', 'price', 'stock']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Thiếu trường dữ liệu: {field}'}), 400
    
    try:
        # Tạo sản phẩm mới
        product = Product(
            name=data['name'],
            price=data['price'],
            stock=data['stock'],
            description=data.get('description', '')
        )
        
        # Lưu vào database
        db.session.add(product)
        db.session.commit()
        
        result = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock,
            'description': product.description,
            'created_at': product.created_at.isoformat()
        }
        
        logger.info(f"Đã tạo sản phẩm mới: {product.name}")
        return jsonify(result), 201
        
    except Exception as e:
        logger.exception(f"Lỗi khi tạo sản phẩm mới: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Lỗi khi tạo sản phẩm mới: {str(e)}'}), 500

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Cập nhật thông tin sản phẩm"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Không có dữ liệu được gửi'}), 400
    
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': f'Không tìm thấy sản phẩm với ID: {product_id}'}), 404
        
        # Cập nhật thông tin sản phẩm
        if 'name' in data:
            product.name = data['name']
        if 'price' in data:
            product.price = data['price']
        if 'stock' in data:
            product.stock = data['stock']
        if 'description' in data:
            product.description = data['description']
        
        db.session.commit()
        
        result = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock,
            'description': product.description,
            'created_at': product.created_at.isoformat()
        }
        
        logger.info(f"Đã cập nhật sản phẩm: {product.name}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi cập nhật sản phẩm {product_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Lỗi khi cập nhật sản phẩm: {str(e)}'}), 500

@app.route('/check', methods=['POST'])
def check_inventory():
    """Kiểm tra tồn kho cho các sản phẩm"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Không có dữ liệu được gửi'}), 400
    
    if not isinstance(data, list):
        return jsonify({'error': 'Dữ liệu phải là một danh sách các sản phẩm'}), 400
    
    try:
        result = []
        all_available = True
        
        for item in data:
            if 'product_id' not in item or 'quantity' not in item:
                return jsonify({'error': 'Các mục phải có product_id và quantity'}), 400
            
            product_id = item['product_id']
            quantity = item['quantity']
            
            product = Product.query.get(product_id)
            
            if not product:
                result.append({
                    'product_id': product_id,
                    'available': False,
                    'message': f'Sản phẩm không tồn tại'
                })
                all_available = False
                continue
            
            if product.stock < quantity:
                result.append({
                    'product_id': product_id,
                    'available': False,
                    'message': f'Không đủ tồn kho (yêu cầu: {quantity}, hiện có: {product.stock})'
                })
                all_available = False
            else:
                result.append({
                    'product_id': product_id,
                    'available': True,
                    'current_stock': product.stock
                })
        
        return jsonify({
            'all_available': all_available,
            'items': result
        }), 200 if all_available else 400
        
    except Exception as e:
        logger.exception(f"Lỗi khi kiểm tra tồn kho: {str(e)}")
        return jsonify({'error': f'Lỗi khi kiểm tra tồn kho: {str(e)}'}), 500

@app.route('/update', methods=['POST'])
def update_inventory():
    """Cập nhật tồn kho cho các sản phẩm"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Không có dữ liệu được gửi'}), 400
    
    if not isinstance(data, list):
        return jsonify({'error': 'Dữ liệu phải là một danh sách các sản phẩm'}), 400
    
    try:
        result = []
        transaction_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        
        for item in data:
            if 'product_id' not in item or 'quantity' not in item:
                return jsonify({'error': 'Các mục phải có product_id và quantity'}), 400
            
            product_id = item['product_id']
            quantity = item['quantity']
            
            product = Product.query.get(product_id)
            
            if not product:
                result.append({
                    'product_id': product_id,
                    'success': False,
                    'message': f'Sản phẩm không tồn tại'
                })
                continue
            
            if product.stock < quantity:
                result.append({
                    'product_id': product_id,
                    'success': False,
                    'message': f'Không đủ tồn kho (yêu cầu: {quantity}, hiện có: {product.stock})'
                })
                continue
            
            # Cập nhật tồn kho
            prev_stock = product.stock
            product.stock -= quantity
            
            # Tạo giao dịch tồn kho
            transaction = InventoryTransaction(
                transaction_id=transaction_id,
                product_id=product_id,
                quantity=-quantity,  # Giảm tồn kho
                prev_stock=prev_stock,
                new_stock=product.stock,
                transaction_type='order'
            )
            
            db.session.add(transaction)
            
            result.append({
                'product_id': product_id,
                'success': True,
                'prev_stock': prev_stock,
                'new_stock': product.stock
            })
        
        db.session.commit()
        logger.info(f"Đã cập nhật tồn kho, transaction ID: {transaction_id}")
        
        return jsonify({
            'transaction_id': transaction_id,
            'items': result
        }), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi cập nhật tồn kho: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Lỗi khi cập nhật tồn kho: {str(e)}'}), 500

@app.route('/restock', methods=['POST'])
def restock_inventory():
    """Nhập thêm hàng vào tồn kho"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Không có dữ liệu được gửi'}), 400
    
    if not isinstance(data, list):
        return jsonify({'error': 'Dữ liệu phải là một danh sách các sản phẩm'}), 400
    
    try:
        result = []
        transaction_id = f"RST-{uuid.uuid4().hex[:8].upper()}"
        
        for item in data:
            if 'product_id' not in item or 'quantity' not in item:
                return jsonify({'error': 'Các mục phải có product_id và quantity'}), 400
            
            product_id = item['product_id']
            quantity = item['quantity']
            
            if quantity <= 0:
                result.append({
                    'product_id': product_id,
                    'success': False,
                    'message': 'Số lượng phải lớn hơn 0'
                })
                continue
            
            product = Product.query.get(product_id)
            
            if not product:
                result.append({
                    'product_id': product_id,
                    'success': False,
                    'message': f'Sản phẩm không tồn tại'
                })
                continue
            
            # Cập nhật tồn kho
            prev_stock = product.stock
            product.stock += quantity
            
            # Tạo giao dịch tồn kho
            transaction = InventoryTransaction(
                transaction_id=transaction_id,
                product_id=product_id,
                quantity=quantity,  # Tăng tồn kho
                prev_stock=prev_stock,
                new_stock=product.stock,
                transaction_type='restock'
            )
            
            db.session.add(transaction)
            
            result.append({
                'product_id': product_id,
                'success': True,
                'prev_stock': prev_stock,
                'new_stock': product.stock
            })
        
        db.session.commit()
        logger.info(f"Đã nhập thêm hàng vào tồn kho, transaction ID: {transaction_id}")
        
        return jsonify({
            'transaction_id': transaction_id,
            'items': result
        }), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi nhập thêm hàng vào tồn kho: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Lỗi khi nhập thêm hàng vào tồn kho: {str(e)}'}), 500

@app.route('/transactions', methods=['GET'])
def get_transactions():
    """Lấy lịch sử giao dịch tồn kho"""
    try:
        product_id = request.args.get('product_id')
        transaction_type = request.args.get('type')
        
        # Tạo query
        query = InventoryTransaction.query
        
        # Thêm filter nếu có
        if product_id:
            query = query.filter_by(product_id=product_id)
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
        
        # Thực hiện query và lấy kết quả
        transactions = query.order_by(InventoryTransaction.created_at.desc()).all()
        
        result = [{
            'id': transaction.id,
            'transaction_id': transaction.transaction_id,
            'product_id': transaction.product_id,
            'quantity': transaction.quantity,
            'prev_stock': transaction.prev_stock,
            'new_stock': transaction.new_stock,
            'transaction_type': transaction.transaction_type,
            'created_at': transaction.created_at.isoformat()
        } for transaction in transactions]
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.exception(f"Lỗi khi lấy lịch sử giao dịch tồn kho: {str(e)}")
        return jsonify({'error': f'Lỗi khi lấy lịch sử giao dịch tồn kho: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Kiểm tra trạng thái dịch vụ"""
    return jsonify({
        'status': 'ok',
        'service': 'inventory',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=True)
