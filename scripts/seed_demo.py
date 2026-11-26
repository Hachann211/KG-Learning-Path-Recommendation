from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.services.seed import seed_demo
app = create_app()
with app.app_context():
    seed_demo()
    print('Demo dataset ready (idempotent).')
