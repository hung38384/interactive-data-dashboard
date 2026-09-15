import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

class SimpleFinancialData:
    def __init__(self):
        # Các cổ phiếu phổ biến để demo
        self.stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META']
        self.data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        
        # Tạo thư mục data nếu chưa có
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
    
    def get_stock_data(self, symbol, period='3mo'):
        """Lấy dữ liệu 1 cổ phiếu"""
        try:
            print(f"Đang lấy dữ liệu {symbol}...")
            stock = yf.Ticker(symbol)
            
            # Lấy historical data
            hist_data = stock.history(period=period)
            
            # Lấy thông tin công ty
            info = stock.info
            
            # Thêm thông tin bổ sung
            hist_data['Symbol'] = symbol
            hist_data['Company'] = info.get('longName', symbol)
            hist_data['Sector'] = info.get('sector', 'Unknown')
            
            return hist_data
            
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu {symbol}: {e}")
            return None
    
    def get_all_stocks_data(self):
        """Lấy dữ liệu tất cả cổ phiếu"""
        all_data = []
        
        for symbol in self.stocks:
            data = self.get_stock_data(symbol)
            if data is not None and not data.empty:
                data = data.reset_index()
                all_data.append(data)
                # Lưu từng file riêng
                self.save_to_csv(data, f"{symbol}_data.csv")
        
        if all_data:
            # Gộp tất cả data
            combined_data = pd.concat(all_data, ignore_index=True)
            
            # Lưu file tổng hợp
            self.save_to_csv(combined_data, "all_stocks_data.csv")
            
            print(f"✅ Đã lấy dữ liệu {len(all_data)} cổ phiếu thành công!")
            return combined_data
        
        return pd.DataFrame()
    
    def save_to_csv(self, data, filename):
        """Lưu dữ liệu ra file CSV"""
        filepath = os.path.join(self.data_folder, filename)
        
        # Reset index để Date thành column
        data_to_save = data.reset_index()
        
        # Lưu file
        data_to_save.to_csv(filepath, index=False)
        print(f"💾 Đã lưu: {filepath}")
    
    def load_from_csv(self, filename):
        """Đọc dữ liệu từ CSV"""
        filepath = os.path.join(self.data_folder, filename)
        
        if os.path.exists(filepath):
            data = pd.read_csv(filepath)
            # Convert Date column back to datetime
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
            return data
        else:
            print(f"File {filepath} không tồn tại")
            return pd.DataFrame()
    
    def get_market_summary(self):
        """Tạo summary của thị trường"""
        try:
            # Lấy data từ file đã lưu
            all_data = self.load_from_csv("all_stocks_data.csv")
            
            if all_data.empty:
                print("Không có dữ liệu. Hãy chạy get_all_stocks_data() trước.")
                return None
            
            # Lấy dữ liệu mới nhất của mỗi cổ phiếu
            latest_data = all_data.groupby('Symbol').tail(1)
            
            summary = []
            for _, row in latest_data.iterrows():
                # Tính % thay đổi (simplified)
                symbol_data = all_data[all_data['Symbol'] == row['Symbol']]
                if len(symbol_data) >= 2:
                    prev_close = symbol_data.iloc[-2]['Close']
                    current_close = row['Close']
                    change_pct = ((current_close - prev_close) / prev_close) * 100
                else:
                    change_pct = 0
                
                summary.append({
                    'Symbol': row['Symbol'],
                    'Company': row['Company'],
                    'Price': round(row['Close'], 2),
                    'Change%': round(change_pct, 2),
                    'Volume': int(row['Volume']),
                    'Date': row['Date']
                })
            
            summary_df = pd.DataFrame(summary)
            
            # Lưu summary
            summary_df.to_csv(os.path.join(self.data_folder, 'market_summary.csv'), index=False)
            
            return summary_df
            
        except Exception as e:
            print(f"Lỗi khi tạo market summary: {e}")
            return None

# Test function
def test_data_collection():
    """Hàm test để kiểm tra"""
    collector = SimpleFinancialData()
    
    print("🚀 Bắt đầu thu thập dữ liệu...")
    
    # Lấy dữ liệu tất cả stocks
    data = collector.get_all_stocks_data()
    
    if not data.empty:
        print(f"\n📊 Thống kê:")
        print(f"- Tổng số records: {len(data)}")
        print(f"- Số cổ phiếu: {data['Symbol'].nunique()}")
        
        # ✅ Đảm bảo Date là cột, không phải index
        data.reset_index(inplace=True)
        print(f"- Ngày từ: {data['Date'].min()}")
        print(f"- Ngày đến: {data['Date'].max()}")
        
        # Tạo market summary
        print("\n📈 Tạo market summary...")
        summary = collector.get_market_summary()
        
        if summary is not None:
            print("\n🎯 Market Summary:")
            print(summary.to_string(index=False))
    
    print("\n✅ Hoàn thành!")

if __name__ == "__main__":
    # Chạy test
    test_data_collection()