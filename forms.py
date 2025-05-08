from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, Email, Length, ValidationError
import re

class MobileNumberForm(FlaskForm):
    mobile_number = StringField('رقم الهاتف', validators=[
        DataRequired('يرجى إدخال رقم الهاتف'),
        Length(min=8, max=8, message='يجب أن يتكون رقم الهاتف من 8 أرقام')
    ])
    submit = SubmitField('استعلام')

    def validate_mobile_number(form, field):
        if not field.data.isdigit():
            raise ValidationError('يجب أن يحتوي رقم الهاتف على أرقام فقط')
        if not (field.data.startswith('3') or field.data.startswith('5') or field.data.startswith('6') or field.data.startswith('7')):
            raise ValidationError('يجب أن يبدأ رقم الهاتف بـ 3 أو 5 أو 6 أو 7')

class BillPaymentForm(FlaskForm):
    mobile_number = StringField('رقم الهاتف', validators=[
        DataRequired('يرجى إدخال رقم الهاتف'),
        Length(min=8, max=8, message='يجب أن يتكون رقم الهاتف من 8 أرقام')
    ])
    submit = SubmitField('استعلام')

    def validate_mobile_number(form, field):
        if not field.data.isdigit():
            raise ValidationError('يجب أن يحتوي رقم الهاتف على أرقام فقط')
        if not (field.data.startswith('3') or field.data.startswith('5') or field.data.startswith('6') or field.data.startswith('7')):
            raise ValidationError('يجب أن يبدأ رقم الهاتف بـ 3 أو 5 أو 6 أو 7')

class RechargeForm(FlaskForm):
    mobile_number = StringField('رقم الهاتف', validators=[
        DataRequired('يرجى إدخال رقم الهاتف'),
        Length(min=8, max=8, message='يجب أن يتكون رقم الهاتف من 8 أرقام')
    ])
    package = SelectField('اختر الباقة', choices=[], validators=[])  # جعل اختيار الباقة غير إجباري
    custom_amount = StringField('مبلغ مخصص (ر.ق)', validators=[])  # إضافة حقل للمبلغ المخصص
    submit = SubmitField('شراء الباقة')

    def validate_mobile_number(form, field):
        if not field.data.isdigit():
            raise ValidationError('يجب أن يحتوي رقم الهاتف على أرقام فقط')
        if not (field.data.startswith('3') or field.data.startswith('5') or field.data.startswith('6') or field.data.startswith('7')):
            raise ValidationError('يجب أن يبدأ رقم الهاتف بـ 3 أو 5 أو 6 أو 7')
    
    def validate_custom_amount(form, field):
        # إذا لم يتم اختيار باقة وتم إدخال مبلغ مخصص
        if not form.package.data and field.data:
            try:
                amount = float(field.data)
                # تم إزالة قيد الحد الأدنى للمبلغ
            except ValueError:
                raise ValidationError('يرجى إدخال مبلغ صحيح')
    
    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False
        
        # إذا تم إدخال مبلغ مخصص ولكنه ليس رقماً صحيحاً
        if self.custom_amount.data and not self.custom_amount.data.isdigit():
            self.custom_amount.errors = ['يرجى إدخال مبلغ صحيح']
            return False
            
        # إذا لم يتم اختيار باقة ولم يتم إدخال مبلغ مخصص، نستخدم مبلغاً افتراضياً
        if not self.package.data and not self.custom_amount.data:
            self.custom_amount.data = "10" # مبلغ افتراضي: 10 ر.ق
            
        return True

class PaymentForm(FlaskForm):
    card_number = StringField('رقم البطاقة', validators=[
        DataRequired('يرجى إدخال رقم البطاقة')
    ])
    expiry_date = StringField('تاريخ الانتهاء (MM/YY)', validators=[
        DataRequired('يرجى إدخال تاريخ انتهاء البطاقة'),
        Length(min=5, max=5, message='يرجى إدخال تاريخ الانتهاء بالصيغة التالية: MM/YY')
    ])
    cvv = StringField('رمز الأمان CVV', validators=[
        DataRequired('يرجى إدخال رمز الأمان'),
        Length(min=3, max=3, message='يجب أن يتكون رمز الأمان من 3 أرقام')
    ])
    cardholder_name = StringField('اسم حامل البطاقة', validators=[
        DataRequired('يرجى إدخال اسم حامل البطاقة')
    ])
    amount = HiddenField('المبلغ')
    mobile_number = HiddenField('رقم الهاتف')
    submit = SubmitField('إتمام الدفع')

    def validate_card_number(form, field):
        # Remove spaces from card number before validation
        card_number = field.data.replace(' ', '')
        if not card_number.isdigit():
            raise ValidationError('يجب أن يحتوي رقم البطاقة على أرقام فقط')
        if len(card_number) != 16:
            raise ValidationError('يجب أن يتكون رقم البطاقة من 16 رقم')

    def validate_cvv(form, field):
        if not field.data.isdigit():
            raise ValidationError('يجب أن يحتوي رمز الأمان على أرقام فقط')

    def validate_expiry_date(form, field):
        if not re.match(r'^\d{2}/\d{2}$', field.data):
            raise ValidationError('يرجى إدخال تاريخ الانتهاء بالصيغة التالية: MM/YY')

class OTPForm(FlaskForm):
    otp = StringField('رمز التحقق', validators=[
        DataRequired('يرجى إدخال رمز التحقق')
        # تم إزالة تقييد طول رمز التحقق
    ])
    transaction_id = HiddenField('رقم العملية')
    otp_step = HiddenField('خطوة التحقق')
    submit = SubmitField('تأكيد')
    
class AdminLoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[
        DataRequired('يرجى إدخال اسم المستخدم')
    ])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired('يرجى إدخال كلمة المرور')
    ])
    submit = SubmitField('تسجيل الدخول')
    # خاصية لتحديد ما إذا كانت العملية قد اكتملت بنجاح
    transaction_completed = False

    # تم إزالة التحقق من أن الرمز يحتوي على أرقام فقط
