import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.services.sync_service import sync_courses, sync_curricula
parser = argparse.ArgumentParser()
parser.add_argument('--query',default='lập trình')
parser.add_argument('--curricula',action='store_true')
parser.add_argument('--cohort',default='K66 - 2024')
args = parser.parse_args()
app = create_app()
with app.app_context():
    job = sync_curricula(args.cohort) if args.curricula else sync_courses(args.query)
    print(f'{job.status}: {job.records} records; source={job.source}')
    if job.status!='success':
        print(job.detail.get('error'))
        raise SystemExit(1)
