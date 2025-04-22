from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class PaymentTransaction(db.Model):
    """Model cho các giao dịch thanh toán"""
    
    __tablename__ = 'payment_transactions'
    
    id = db.Column(db.String(20), primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    customer_id = db.Column(db.String(50), nullable=False)
    
    # Thời gian
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Thông tin hoàn tiền
    refunded = db.Column(db.Boolean, default=False)
    refunded_at = db.Column(db.DateTime, nullable=True)
    refund_reason = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f"<Payment {self.id} - {self.amount} - {self.status}>"
