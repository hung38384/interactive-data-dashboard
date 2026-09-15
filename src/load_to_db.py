import os
import pandas as pd
from sqlalchemy import create_engine

# Đường dẫn tới thư mục chứa CSV
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# Ensure database directory exists
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database')
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Tạo kết nối tới SQLite (sẽ tạo file stock_data.db nếu chưa có)
db_path = os.path.join(DB_DIR, 'stock_data.db')
engine = create_engine(f'sqlite:///{db_path}')

# Hàm làm sạch và load dữ liệu
def load_csv_to_sqlite():
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('_data.csv') or filename == 'market_summary.csv':
            filepath = os.path.join(DATA_DIR, filename)
            table_name = filename.replace('.csv', '').lower()

            print(f"Đang xử lý {filename} -> bảng {table_name}")

            # Đọc file CSV
            df = pd.read_csv(filepath)

            # --- TRANSFORM ---
            # Chuẩn hóa cột ngày
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            # Loại bỏ dòng thiếu dữ liệu
            df = df.dropna()

            # Đổi kiểu các cột số (nếu cần)
            for col in df.select_dtypes(include='object').columns:
                if col not in ['Date', 'Name', 'Symbol']:
                    try:
                        df[col] = df[col].str.replace(',', '').astype(float)
                    except:
                        pass

            # --- LOAD ---
            df.to_sql(table_name, con=engine, if_exists='replace', index=False)
            print(f"✓ Đã load {filename} vào bảng {table_name}")

if __name__ == '__main__':
    load_csv_to_sqlite()