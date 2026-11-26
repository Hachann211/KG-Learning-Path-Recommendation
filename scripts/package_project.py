"""Package a local demo snapshot, allowing only the explicitly public demo accounts."""
import json
import os
from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
import zipfile
from werkzeug.security import check_password_hash

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.services.customer_demo import DEMO_MARKER, demo_accounts


def validate_demo_users(connection):
    accounts={a['email']:a for a in demo_accounts()}
    for email,role,profile,password_hash in connection.execute('SELECT email,role,profile,password_hash FROM users'):
        account=accounts.get(email)
        if not account or role!=account['role'] or json.loads(profile or '{}').get('demo_seed')!=DEMO_MARKER:
            raise ValueError('Refusing to package personal accounts. Only explicitly tagged customer-demo accounts are allowed.')
        if not check_password_hash(password_hash,account['password']):
            raise ValueError('Demo passwords have changed. Run scripts/prepare_demo.py --reset before packaging the public demo.')


def package_project(root=ROOT):
    target=root/'neu-learning-path.zip'
    # Build and validate a consistent SQLite backup before touching the existing deliverable.
    with tempfile.TemporaryDirectory(dir=root/'instance') as temp:
        snapshot=Path(temp)/'learning.db'
        with closing(sqlite3.connect(str(root/'instance/learning.db'))) as source, closing(sqlite3.connect(str(snapshot))) as connection:
            source.backup(connection)
            validate_demo_users(connection)
            if connection.execute('PRAGMA foreign_key_check').fetchone():
                raise ValueError('Cannot package a database with broken references.')
        temporary_archive=Path(temp)/target.name
        with zipfile.ZipFile(temporary_archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for folder in ['app','scripts','tests','migrations','docs']:
                for path in (root/folder).rglob('*'):
                    if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ['.pyc','.log']:
                        archive.write(path,path.relative_to(root))
            for filename in ['README.md','requirements.txt','pytest.ini','run.py','start.bat','.env.example','.gitignore']:
                archive.write(root/filename,filename)
            archive.write(snapshot,'instance/learning.db')
        os.replace(temporary_archive,target)
    return target


if __name__=='__main__':
    try:
        target=package_project()
        print(target.name,target.stat().st_size,'bytes; public demo accounts included; no personal accounts, .env or instance secret')
    except ValueError as error:
        raise SystemExit(str(error)) from error
