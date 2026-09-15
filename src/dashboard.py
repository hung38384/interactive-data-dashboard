import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import os
from datetime import datetime, timedelta

class FinancialDashboard:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        self.setup_layout()
        self.setup_callbacks()
    
    def load_data(self):
        """Load dữ liệu từ CSV files"""
        try:
            # Load all stocks data
            all_data_path = os.path.join(self.data_folder, 'all_stocks_data.csv')
            if os.path.exists(all_data_path):
                data = pd.read_csv(all_data_path)
                data['Date'] = pd.to_datetime(data['Date'])
                return data
            else:
                print("Không tìm thấy file dữ liệu. Hãy chạy data_collector.py trước!")
                return pd.DataFrame()
        except Exception as e:
            print(f"Lỗi khi load dữ liệu: {e}")
            return pd.DataFrame()
    
    def get_stock_options(self):
        """Lấy danh sách stocks để làm dropdown options"""
        data = self.load_data()
        if not data.empty:
            stocks = data[['Symbol', 'Company']].drop_duplicates()
            return [{'label': f"{row['Company']} ({row['Symbol']})", 'value': row['Symbol']} 
                   for _, row in stocks.iterrows()]
        return []
    
    def setup_layout(self):
        """Thiết lập layout cho dashboard"""
        
        # Colors and styling
        colors = {
            'background': '#1f2937',
            'surface': '#374151',
            'text': '#f9fafb',
            'primary': '#3b82f6',
            'success': '#10b981',
            'danger': '#ef4444'
        }
        
        self.app.layout = html.Div([
            
            # Header
            html.Div([
                html.H1("📈 Financial Data Dashboard", 
                       className="text-4xl font-bold text-center mb-8 text-white"),
                html.P("Real-time Stock Market Analysis", 
                      className="text-center text-gray-300 mb-8")
            ], className="bg-gray-800 p-6"),
            
            # Controls Section
            html.Div([
                html.Div([
                    html.Label("Select Stock:", className="block text-sm font-medium text-gray-700 mb-2"),
                    dcc.Dropdown(
                        id='stock-dropdown',
                        options=self.get_stock_options(),
                        value='AAPL',
                        className="mb-4"
                    ),
                ], className="w-full md:w-1/3 px-2"),
                
                html.Div([
                    html.Label("Time Period:", className="block text-sm font-medium text-gray-700 mb-2"),
                    dcc.Dropdown(
                        id='period-dropdown',
                        options=[
                            {'label': 'Last 7 Days', 'value': 7},
                            {'label': 'Last 30 Days', 'value': 30},
                            {'label': 'Last 60 Days', 'value': 60},
                            {'label': 'All Time', 'value': 0}
                        ],
                        value=30,
                        className="mb-4"
                    )
                ], className="w-full md:w-1/3 px-2"),
                
                html.Div([
                    html.Label("Chart Type:", className="block text-sm font-medium text-gray-700 mb-2"),
                    dcc.Dropdown(
                        id='chart-type-dropdown',
                        options=[
                            {'label': 'Line Chart', 'value': 'line'},
                            {'label': 'Candlestick', 'value': 'candlestick'},
                            {'label': 'Area Chart', 'value': 'area'}
                        ],
                        value='line',
                        className="mb-4"
                    )
                ], className="w-full md:w-1/3 px-2"),
                
            ], className="flex flex-wrap bg-white p-4 shadow-md"),
            
            # Summary Cards
            html.Div(id='summary-cards', className="p-4"),
            
            # Main Charts
            html.Div([
                # Price Chart
                html.Div([
                    dcc.Graph(id='price-chart', className="h-96")
                ], className="w-full lg:w-2/3 p-2"),
                
                # Volume Chart
                html.Div([
                    dcc.Graph(id='volume-chart', className="h-96")
                ], className="w-full lg:w-1/3 p-2"),
                
            ], className="flex flex-wrap"),
            
            # Market Overview Table
            html.Div([
                html.H3("Market Overview", className="text-xl font-bold mb-4"),
                html.Div(id='market-table')
            ], className="p-4 bg-white m-4 rounded shadow"),
            
            # Auto refresh
            dcc.Interval(
                id='interval-component',
                interval=60*1000,  # Update every minute
                n_intervals=0
            )
            
        ], className="min-h-screen bg-gray-100")
    
    def setup_callbacks(self):
        """Setup các callback functions"""
        
        @self.app.callback(
            [Output('price-chart', 'figure'),
             Output('volume-chart', 'figure'),
             Output('summary-cards', 'children'),
             Output('market-table', 'children')],
            [Input('stock-dropdown', 'value'),
             Input('period-dropdown', 'value'),
             Input('chart-type-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(selected_stock, period, chart_type, n):
            return self.update_charts_and_data(selected_stock, period, chart_type)
    
    def update_charts_and_data(self, selected_stock, period, chart_type):
        """Update tất cả charts và data"""
        
        # Load data
        all_data = self.load_data()
        
        if all_data.empty:
            empty_fig = go.Figure()
            empty_fig.update_layout(title="No Data Available")
            return empty_fig, empty_fig, html.Div("No data"), html.Div("No data")
        
        # Filter data cho stock được chọn
        stock_data = all_data[all_data['Symbol'] == selected_stock].copy()
        stock_data = stock_data.sort_values('Date')
        
        # Filter theo thời gian
        if period > 0:
            cutoff_date = stock_data['Date'].max() - timedelta(days=period)
            stock_data = stock_data[stock_data['Date'] >= cutoff_date]
        
        if stock_data.empty:
            empty_fig = go.Figure()
            empty_fig.update_layout(title=f"No Data for {selected_stock}")
            return empty_fig, empty_fig, html.Div("No data"), html.Div("No data")
        
        # Tạo price chart
        price_fig = self.create_price_chart(stock_data, selected_stock, chart_type)
        
        # Tạo volume chart
        volume_fig = self.create_volume_chart(stock_data, selected_stock)
        
        # Tạo summary cards
        summary_cards = self.create_summary_cards(stock_data, selected_stock)
        
        # Tạo market table
        market_table = self.create_market_table(all_data)
        
        return price_fig, volume_fig, summary_cards, market_table
    
    def create_price_chart(self, data, symbol, chart_type):
        """Tạo price chart"""
        
        fig = go.Figure()
        
        if chart_type == 'line':
            fig.add_trace(go.Scatter(
                x=data['Date'],
                y=data['Close'],
                mode='lines',
                name='Close Price',
                line=dict(color='#3b82f6', width=2),
                hovertemplate='Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
            ))
            
        elif chart_type == 'candlestick':
            fig.add_trace(go.Candlestick(
                x=data['Date'],
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='OHLC'
            ))
            
        elif chart_type == 'area':
            fig.add_trace(go.Scatter(
                x=data['Date'],
                y=data['Close'],
                fill='tozeroy',
                mode='lines',
                name='Close Price',
                line=dict(color='#3b82f6'),
                fillcolor='rgba(59, 130, 246, 0.3)'
            ))
        
        fig.update_layout(
            title=f'{symbol} Stock Price',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        return fig
    
    def create_volume_chart(self, data, symbol):
        """Tạo volume chart"""
        
        fig = go.Figure()
        
        # Color bars based on price movement
        colors = ['green' if close >= open else 'red' 
                 for close, open in zip(data['Close'], data['Open'])]
        
        fig.add_trace(go.Bar(
            x=data['Date'],
            y=data['Volume'],
            name='Volume',
            marker_color=colors,
            hovertemplate='Date: %{x}<br>Volume: %{y:,}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'{symbol} Trading Volume',
            xaxis_title='Date',
            yaxis_title='Volume',
            template='plotly_white',
            height=400
        )
        
        return fig
    
    def create_summary_cards(self, data, symbol):
        """Tạo summary cards"""
        
        if len(data) < 2:
            return html.Div("Insufficient data")
        
        latest = data.iloc[-1]
        previous = data.iloc[-2]
        
        current_price = latest['Close']
        change = current_price - previous['Close']
        change_pct = (change / previous['Close']) * 100
        
        # Determine color based on change
        change_color = 'text-green-600' if change >= 0 else 'text-red-600'
        change_icon = '📈' if change >= 0 else '📉'
        
        cards = html.Div([
            
            # Current Price Card
            html.Div([
                html.H3("Current Price", className="text-sm font-medium text-gray-500"),
                html.P(f"${current_price:.2f}", className="text-2xl font-bold")
            ], className="bg-white p-4 rounded-lg shadow"),
            
            # Change Card
            html.Div([
                html.H3("Change", className="text-sm font-medium text-gray-500"),
                html.P([
                    f"{change_icon} ${change:.2f} ({change_pct:.2f}%)"
                ], className=f"text-2xl font-bold {change_color}")
            ], className="bg-white p-4 rounded-lg shadow"),
            
            # Volume Card
            html.Div([
                html.H3("Volume", className="text-sm font-medium text-gray-500"),
                html.P(f"{latest['Volume']:,}", className="text-2xl font-bold")
            ], className="bg-white p-4 rounded-lg shadow"),
            
            # High/Low Card
            html.Div([
                html.H3("Day Range", className="text-sm font-medium text-gray-500"),
                html.P(f"${latest['Low']:.2f} - ${latest['High']:.2f}", 
                      className="text-2xl font-bold")
            ], className="bg-white p-4 rounded-lg shadow"),
            
        ], className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6")
        
        return cards
    
    def create_market_table(self, all_data):
        """Tạo market overview table"""
        
        # Get latest data for each stock
        latest_data = all_data.loc[all_data.groupby('Symbol')['Date'].idxmax()]
        
        # Calculate changes
        table_data = []
        for _, stock in latest_data.iterrows():
            symbol = stock['Symbol']
            stock_history = all_data[all_data['Symbol'] == symbol].sort_values('Date')
            
            if len(stock_history) >= 2:
                current_price = stock_history.iloc[-1]['Close']
                prev_price = stock_history.iloc[-2]['Close']
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100
            else:
                current_price = stock['Close']
                change = 0
                change_pct = 0
            
            table_data.append({
                'Symbol': symbol,
                'Company': stock['Company'],
                'Price': f"${current_price:.2f}",
                'Change': f"${change:.2f}",
                'Change %': f"{change_pct:.2f}%",
                'Volume': f"{stock['Volume']:,}"
            })
        
        # Create DataTable
        table = dash_table.DataTable(
            data=table_data,
            columns=[
                {'name': 'Symbol', 'id': 'Symbol'},
                {'name': 'Company', 'id': 'Company'},
                {'name': 'Price', 'id': 'Price'},
                {'name': 'Change', 'id': 'Change'},
                {'name': 'Change %', 'id': 'Change %'},
                {'name': 'Volume', 'id': 'Volume'}
            ],
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': '#f3f4f6', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{Change %} > 0'},
                    'backgroundColor': '#dcfce7',
                    'color': '#166534',
                },
                {
                    'if': {'filter_query': '{Change %} < 0'},
                    'backgroundColor': '#fee2e2',
                    'color': '#dc2626',
                }
            ]
        )
        
        return table
    
    def run(self, debug=True, port=8050):
        """Chạy dashboard"""
        print("🚀 Starting Financial Dashboard...")
        print(f"📊 Open browser and go to: http://localhost:{port}")
        self.app.run(debug=debug, port=port)

# Main execution
if __name__ == '__main__':
    dashboard = FinancialDashboard()
    dashboard.run()