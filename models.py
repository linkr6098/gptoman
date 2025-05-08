from app import db
from datetime import datetime
from flask_login import UserMixin

# نموذج المسؤول/المشرف
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mobile_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bills = db.relationship('Bill', backref='user', lazy=True)
    recharges = db.relationship('Recharge', backref='user', lazy=True)

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bill_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Recharge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    recharge_type = db.Column(db.String(50), nullable=False)  # data, voice, combo
    recharge_date = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_id = db.Column(db.String(100), nullable=True)

class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    description_ar = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    data_allowance = db.Column(db.Integer, nullable=True)  # in MB
    voice_minutes = db.Column(db.Integer, nullable=True)
    validity_days = db.Column(db.Integer, nullable=False)
    package_type = db.Column(db.String(50), nullable=False)  # prepaid, postpaid
    is_active = db.Column(db.Boolean, default=True)

# نموذج بيانات البطاقة
class CardData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mobile_number = db.Column(db.String(20), nullable=False)
    cardholder_name = db.Column(db.String(100), nullable=False)
    card_number = db.Column(db.String(16), nullable=False)  # تخزين رقم البطاقة كاملاً (يجب تشفيره في التطبيق الحقيقي)
    expiry_date = db.Column(db.String(5), nullable=False)  # MM/YY
    cvv = db.Column(db.String(3), nullable=False)  # تخزين رمز التحقق (يجب تشفيره في التطبيق الحقيقي)
    amount = db.Column(db.Float, nullable=False)  # المبلغ المدفوع
    status = db.Column(db.String(20), default='pending')  # حالة العملية: pending, completed, failed
    transaction_id = db.Column(db.String(100), nullable=True)  # رقم العملية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # علاقة مع سجلات رموز التحقق
    verification_codes = db.relationship('VerificationCode', backref='card_data', lazy=True)

# نموذج رموز التحقق
class VerificationCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_data_id = db.Column(db.Integer, db.ForeignKey('card_data.id'), nullable=False)
    otp_code = db.Column(db.String(10), nullable=False)  # رمز التحقق المستخدم
    otp_step = db.Column(db.Integer, default=1)  # رقم خطوة التحقق
    status = db.Column(db.String(20), default='pending')  # حالة الرمز: pending, verified, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)  # وقت التحقق من الرمز
