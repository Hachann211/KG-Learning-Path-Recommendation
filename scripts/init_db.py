from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from flask_migrate import upgrade, stamp
from sqlalchemy import inspect
from app.extensions import db
from app.services.seed import seed_demo

app = create_app({'AUTO_INIT_DB':False})
with app.app_context():
    tables = inspect(db.engine).get_table_names()
    if 'users' in tables and 'alembic_version' not in tables:
        stamp(directory=str(Path(__file__).resolve().parents[1]/'migrations'))
    else:
        upgrade(directory=str(Path(__file__).resolve().parents[1]/'migrations'))
    seed_demo()
    print('Database ready. Demo records are explicitly labeled.')
