import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///ooredoo.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models and routes
    import models  # noqa: F401
    from routes import *  # noqa: F401, F403

    # Create tables
    db.create_all()
    
    # إنشاء حساب المسؤول إذا لم يكن موجودًا
    from models import Admin
    from werkzeug.security import generate_password_hash
    if Admin.query.count() == 0:
        admin = Admin(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        
    # إنشاء الباقات الافتراضية إذا لم تكن موجودة
    from models import Package
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
