import schedule
import time
from datetime import datetime
from data_collector import SimpleFinancialData
import pandas as pd
import sqlite3

api = SimpleFinancialData()

def etl_job():
    print(f"[{datetime.now()}] 🔄 Bắt đầu ETL...")

    # 1. Lấy dữ liệu từ API (VD: nhiều mã)
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    all_data = []

    for symbol in symbols:
        try:
            data = api.get_stock_data(symbol)  # ✅ dùng đúng instance method
            if data is not None and not data.empty:
                df = data.reset_index()  # Đảm bảo có cột Date
                df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Symbol']]  # Lấy cột cần thiết
                df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol']  # Đổi tên cho chuẩn DB
                all_data.append(df)
        except Exception as e:
            print(f"Lỗi lấy dữ liệu {symbol}: {e}")

    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)

        # 2. Chuyển đổi dữ liệu
        full_df['date'] = pd.to_datetime(full_df['date'], errors='coerce')
        num_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in num_cols:
            full_df[col] = pd.to_numeric(full_df[col], errors='coerce')

        full_df.dropna(inplace=True)

        # 3. Lưu vào SQLite
        conn = sqlite3.connect('stock_data.db')
        full_df.to_sql('stocks', conn, if_exists='append', index=False)
        conn.close()

        print(f"[{datetime.now()}] ✅ Đã lưu {len(full_df)} dòng mới vào DB.")
    else:
        print("❌ Không có dữ liệu để lưu.")

# Chạy thử mỗi 1 phút (để test)
schedule.every(1).minutes.do(etl_job)

# Khi deploy thực tế, dùng:
# schedule.every().day.at("09:00").do(etl_job)

if __name__ == "__main__":
    print("🚀 Bắt đầu chạy ETL scheduler...")
    while True:
        schedule.run_pending()
        time.sleep(1)