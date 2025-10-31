import sys
import os

print("Testing deployment readiness...")
print("=" * 50)

errors = []
warnings = []

try:
    import flask
    print("✓ Flask installed")
except ImportError:
    errors.append("Flask not installed")
    print("✗ Flask not installed")

try:
    import numpy
    print("✓ NumPy installed")
except ImportError:
    errors.append("NumPy not installed")
    print("✗ NumPy not installed")

try:
    import pandas
    print("✓ Pandas installed")
except ImportError:
    errors.append("Pandas not installed")
    print("✗ Pandas not installed")

try:
    import sklearn
    print("✓ Scikit-learn installed")
except ImportError:
    errors.append("Scikit-learn not installed")
    print("✗ Scikit-learn not installed")

try:
    import scipy
    print("✓ SciPy installed")
except ImportError:
    errors.append("SciPy not installed")
    print("✗ SciPy not installed")

try:
    import gunicorn
    print("✓ Gunicorn installed")
except ImportError:
    warnings.append("Gunicorn not installed (needed for production)")
    print("⚠ Gunicorn not installed")

print("\nChecking file structure...")
print("=" * 50)

required_files = [
    'app.py',
    'requirements.txt',
    'Procfile',
    'runtime.txt',
    'render.yaml',
    'templates/index.html',
    'static/style.css',
    'static/script.js'
]

for file in required_files:
    if os.path.exists(file):
        print(f"✓ {file}")
    else:
        errors.append(f"Missing file: {file}")
        print(f"✗ {file} missing")

print("\nTesting app imports...")
print("=" * 50)

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app import app, load_or_train_models
    print("✓ App imports successfully")
    
    with app.test_client() as client:
        response = client.get('/')
        if response.status_code == 200:
            print("✓ Home route works")
        else:
            errors.append(f"Home route returned {response.status_code}")
            
except Exception as e:
    errors.append(f"App import error: {str(e)}")
    print(f"✗ App import failed: {str(e)}")

print("\n" + "=" * 50)
if errors:
    print(f"\n✗ Found {len(errors)} errors:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
elif warnings:
    print(f"\n⚠ Found {len(warnings)} warnings:")
    for warning in warnings:
        print(f"  - {warning}")
    print("\n✓ Deployment ready!")
else:
    print("\n✓ All checks passed! Deployment ready!")
    print("\nTo test locally:")
    print("  python app.py")
    print("\nTo deploy:")
    print("  1. Push to GitHub")
    print("  2. Connect to Render")
    print("  3. Deploy!")

