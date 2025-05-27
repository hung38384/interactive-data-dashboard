from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime, timedelta

app = Flask(__name__)
DB_PATH = "stock_data.db"
CORS(app)  # Enable CORS for all routes

class FinancialAPI:
    def __init__(self):
        self.data_folder = 'data'
    
    def load_all_data(self):
        """Load all stocks data"""
        try:
            filepath = '/Users/admin/Desktop/interactive_data_dashboard/src/data/all_stocks_data.csv'
            if os.path.exists(filepath):
                data = pd.read_csv(filepath)
                data['Date'] = pd.to_datetime(data['Date'])
                return data
            else:
                print(f"⚠️ File not found at: {filepath}")
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return pd.DataFrame()
    
    def get_stock_list(self):
        """Get list of available stocks"""
        data = self.load_all_data()
        if not data.empty:
            stocks = data[['Symbol', 'Company']].drop_duplicates()
            return stocks.to_dict('records')
        return []
    
    def get_stock_data(self, symbol, days=None):
        """Get specific stock data"""
        data = self.load_all_data()
        if data.empty:
            return []
        
        # Filter by symbol
        stock_data = data[data['Symbol'].str.upper() == symbol.upper()].copy()
        
        if stock_data.empty:
            return []
        
        # Sort by date
        stock_data = stock_data.sort_values('Date')
        
        # Filter by days if specified
        if days:
            cutoff_date = stock_data['Date'].max() - timedelta(days=days)
            stock_data = stock_data[stock_data['Date'] >= cutoff_date]
        
        # Convert to dict and format dates
        result = []
        for _, row in stock_data.iterrows():
            result.append({
                'date': row['Date'].strftime('%Y-%m-%d'),
                'open': round(row['Open'], 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2),
                'close': round(row['Close'], 2),
                'volume': int(row['Volume']),
                'company': row['Company']
            })
        
        return result
    
    def get_market_summary(self):
        """Get market summary"""
        data = self.load_all_data()
        if data.empty:
            return []
        
        # Get latest data for each stock
        latest_data = data.loc[data.groupby('Symbol')['Date'].idxmax()]
        
        summary = []
        for _, row in latest_data.iterrows():
            # Calculate change (simplified - comparing with previous day if available)
            symbol_data = data[data['Symbol'] == row['Symbol']].sort_values('Date')
            
            if len(symbol_data) >= 2:
                current_price = symbol_data.iloc[-1]['Close']
                prev_price = symbol_data.iloc[-2]['Close']
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100
            else:
                current_price = row['Close']
                change = 0
                change_pct = 0
            
            summary.append({
                'symbol': row['Symbol'],
                'company': row['Company'],
                'price': round(current_price, 2),
                'change': round(change, 2),
                'change_percent': round(change_pct, 2),
                'volume': int(row['Volume']),
                'date': row['Date'].strftime('%Y-%m-%d')
            })
        
        return summary
    
    def get_stock_analytics(self, symbol):
        """Get analytics for a specific stock"""
        data = self.load_all_data()
        if data.empty:
            return {}
        
        stock_data = data[data['Symbol'].str.upper() == symbol.upper()]
        if stock_data.empty:
            return {}
        
        stock_data = stock_data.sort_values('Date')
        
        # Calculate analytics
        current_price = stock_data.iloc[-1]['Close']
        max_price = stock_data['High'].max()
        min_price = stock_data['Low'].min()
        avg_price = stock_data['Close'].mean()
        avg_volume = stock_data['Volume'].mean()
        
        # Calculate volatility (simplified)
        price_changes = stock_data['Close'].pct_change().dropna()
        volatility = price_changes.std() * 100
        
        return {
            'symbol': symbol.upper(),
            'current_price': round(current_price, 2),
            'max_price': round(max_price, 2),
            'min_price': round(min_price, 2),
            'avg_price': round(avg_price, 2),
            'avg_volume': int(avg_volume),
            'volatility': round(volatility, 2),
            'total_records': len(stock_data),
            'date_range': {
                'from': stock_data['Date'].min().strftime('%Y-%m-%d'),
                'to': stock_data['Date'].max().strftime('%Y-%m-%d')
            }
        }
    
    def query_db(query, args=()):
        """Chạy query và trả kết quả dạng dict."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(query, args)
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

# Initialize API
api = FinancialAPI()

# Routes
@app.route('/')
def home():
    """API home page"""
    return jsonify({
        'message': 'Financial Data API',
        'version': '1.0',
        'endpoints': [
            '/api/stocks - Get list of stocks',
            '/api/stocks/<symbol> - Get stock data',
            '/api/market/summary - Get market summary',
            '/api/analytics/<symbol> - Get stock analytics'
        ]
    })

@app.route('/api/stocks')
def get_stocks():
    """Get list of available stocks"""
    try:
        stocks = api.get_stock_list()
        return jsonify({
            'success': True,
            'data': stocks,
            'count': len(stocks)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stocks/<symbol>')
def get_stock_data(symbol):
    """Lấy dữ liệu theo mã chứng khoán và số ngày gần nhất (tuỳ chọn)"""
    symbol = symbol.upper()
    valid_symbols = ['AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN', 'META', 'NVDA']
    if symbol not in valid_symbols:
        return jsonify({
            'success': False,
            'error': f"Mã chứng khoán '{symbol}' không hợp lệ."
        }), 404

    table_name = f"{symbol.lower()}_data"
    days = request.args.get('days', type=int)

    try:
        if days:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            query = f"""
                SELECT * FROM {table_name}
                WHERE date >= ?
                ORDER BY date DESC
            """
            data = query_db(query, (start_date,))
        else:
            query = f"SELECT * FROM {table_name} ORDER BY date DESC LIMIT 50"
            data = query_db(query)

        return jsonify({
            'success': True,
            'symbol': symbol,
            'count': len(data),
            'data': data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/market/summary')
def get_market_summary():
    """Get market summary"""
    try:
        summary = api.get_market_summary()
        return jsonify({
            'success': True,
            'data': summary,
            'count': len(summary),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analytics/<symbol>')
def get_analytics(symbol):
    """Get analytics for specific stock"""
    try:
        analytics = api.get_stock_analytics(symbol)
        
        if not analytics:
            return jsonify({
                'success': False,
                'error': f'No data found for symbol: {symbol}'
            }), 404
        
        return jsonify({
            'success': True,
            'data': analytics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Financial API Server...")
    print("📡 API available at: http://localhost:5001")
    print("📋 Available endpoints:")
    print("  - GET /api/stocks")
    print("  - GET /api/stocks/<symbol>")
    print("  - GET /api/market/summary")
    print("  - GET /api/analytics/<symbol>")
    
    app.run(debug=True, port=5001)