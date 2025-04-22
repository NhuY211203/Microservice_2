from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ShippingOrder(db.Model):
    """Model cho đơn vận chuyển"""
    
    __tablename__ = 'shipping_orders'
    
    id = db.Column(db.String(20), primary_key=True)
    customer_id = db.Column(db.String(50), nullable=False)
    address = db.Column(db.Text, nullable=False)
    items = db.Column(db.Text, nullable=False)  # JSON string
    payment_id = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='processing')
    estimated_delivery = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    
    def __repr__(self):
        return f"<ShippingOrder {self.id} - {self.status}>"

class ShippingStatus(db.Model):
    """Model cho lịch sử trạng thái đơn vận chuyển"""
    
    __tablename__ = 'shipping_statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    shipping_id = db.Column(db.String(20), db.ForeignKey('shipping_orders.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    
    def __repr__(self):
        return f"<ShippingStatus {self.id} - {self.shipping_id} - {self.status}>"

class ShippingLocation(db.Model):
    """Model cho lịch sử vị trí đơn vận chuyển"""
    
    __tablename__ = 'shipping_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    shipping_id = db.Column(db.String(20), db.ForeignKey('shipping_orders.id'), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    
    def __repr__(self):
        return f"<ShippingLocation {self.id} - {self.shipping_id} - {self.location}>"
