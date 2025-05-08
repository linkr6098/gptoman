from app import app, db
from models import Package

with app.app_context():
    packages = Package.query.all()
    print('Number of packages:', len(packages))
    for p in packages:
        print(f'Package {p.id}: {p.name} - {p.name_ar} - {p.price} - {p.package_type}')