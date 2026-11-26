from pathlib import Path
from flask_migrate import upgrade
from sqlalchemy import inspect
from app import create_app
from app.extensions import db

def test_baseline_upgrade_creates_clean_database(tmp_path):
    app=create_app({'TESTING':True,'AUTO_INIT_DB':False,'SQLALCHEMY_DATABASE_URI':'sqlite:///'+str(tmp_path/'migration.db')})
    with app.app_context():
        upgrade(directory=str(Path(__file__).resolve().parents[1]/'migrations'))
        tables=set(inspect(db.engine).get_table_names())
        assert {'users','knowledge_nodes','knowledge_edges','curriculum_courses','learning_paths','alembic_version'} <= tables
        db.engine.dispose()
