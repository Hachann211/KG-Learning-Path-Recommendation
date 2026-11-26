"""Create or promote an admin using an interactive local console, never a hardcoded password."""
from getpass import getpass
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models import User
app = create_app()
with app.app_context():
    email = input('Admin email: ').strip().lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
        raise SystemExit('Invalid email.')
    name = input('Display name: ').strip() or 'Admin'
    password = getpass('New password (at least 12 characters): ')
    if not 12<=len(password)<=128 or password!=getpass('Confirm password: '):
        raise SystemExit('Password too short or confirmation does not match.')
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(email=email,name=name,profile={})
        db.session.add(user)
    user.name = name
    user.role = 'admin'
    user.password_hash = generate_password_hash(password)
    db.session.commit()
    print('Admin is ready. Sign in through the website to open /admin.')
