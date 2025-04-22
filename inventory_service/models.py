from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    """Model cho sản phẩm"""
    
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    
    transactions = db.relationship('InventoryTransaction', backref='product', lazy=True)
    
    def __repr__(self):
        return f"<Product {self.id} - {self.name}>"

class InventoryTransaction(db.Model):
    """Model cho các giao dịch tồn kho"""
    
    __tablename__ = 'inventory_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(20), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)  # Số lượng thay đổi (dương: nhập, âm: xuất)
    prev_stock = db.Column(db.Integer, nullable=False)  # Tồn kho trước giao dịch
    new_stock = db.Column(db.Integer, nullable=False)  # Tồn kho sau giao dịch
    transaction_type = db.Column(db.String(20), nullable=False)  # 'order', 'restock', 'return', 'adjustment'
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    
    def __repr__(self):
        return f"<InventoryTransaction {self.id} - {self.product_id} - {self.quantity}>"
