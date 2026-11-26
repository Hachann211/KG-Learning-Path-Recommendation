"""Create the opt-in local customer demo; --reset restores only marked demo fixtures."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.services.customer_demo import prepare_customer_demo

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chuẩn bị tài khoản, hồ sơ, tiến độ và lộ trình demo.')
    parser.add_argument('--reset',action='store_true',help='Khôi phục mật khẩu và dữ liệu mẫu của hai tài khoản demo đã gắn nhãn.')
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        for account in prepare_customer_demo(reset=args.reset):
            print(f"{account['email']} | {account['role']} | {account['plans']} saved plans | {account['progress']} progress records")
    print('Customer demo ready. Public demo credentials are shown on the login form.')
