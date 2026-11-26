"""Development helper: generate the baseline migration against an empty transient DB."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from alembic.migration import MigrationContext
from alembic.autogenerate import produce_migrations, render_python_code
from app import create_app
from app.extensions import db

app=create_app({'AUTO_INIT_DB':False})
with app.app_context():
    engine=create_engine('sqlite://')
    with engine.connect() as connection:
        context=MigrationContext.configure(connection)
        script=produce_migrations(context,db.metadata)
        up=render_python_code(script.upgrade_ops)
        down=render_python_code(script.downgrade_ops)
    text='''"""Initial relational schema and persisted knowledge graph.

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
'''+up+'\n\ndef downgrade():\n'+down+'\n'
    path=Path(__file__).resolve().parents[1]/'migrations/versions/0001_initial.py'
    path.write_text(text,encoding='utf-8')
    print('Baseline generated:',path.name)
