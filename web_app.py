from flask import Flask, render_template, jsonify, request
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('stock.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html', active_page='kline')

@app.route('/backtest')
def backtest_page():
    return render_template('backtest2.html', active_page='backtest')

@app.route('/api/sectors')
def get_sectors():
    conn = get_db()
    cursor = conn.execute('SELECT DISTINCT sector_level1, sector_level2 FROM stock_sector ORDER BY sector_level1, sector_level2')
    rows = cursor.fetchall()
    
    # 組織成兩層結構
    sectors = {}
    for row in rows:
        level1 = row['sector_level1']
        level2 = row['sector_level2']
        if level1 not in sectors:
            sectors[level1] = []
        if level2 and level2 not in sectors[level1]:
            sectors[level1].append(level2)
    
    conn.close()
    return jsonify(sectors)

@app.route('/api/stocks')
def get_stocks():
    level1 = request.args.get('level1', '全部')
    level2 = request.args.get('level2', '')
    conn = get_db()
    
    if level1 == '全部':
        cursor = conn.execute('SELECT code, name FROM stock_list ORDER BY code')
    elif level2:
        cursor = conn.execute('''
            SELECT sl.code, sl.name 
            FROM stock_list sl
            JOIN stock_sector ss ON sl.code = ss.stock_id
            WHERE ss.sector_level1 = ? AND ss.sector_level2 = ?
            ORDER BY sl.code
        ''', (level1, level2))
    else:
        cursor = conn.execute('''
            SELECT sl.code, sl.name 
            FROM stock_list sl
            JOIN stock_sector ss ON sl.code = ss.stock_id
            WHERE ss.sector_level1 = ?
            ORDER BY sl.code
        ''', (level1,))
    
    rows = cursor.fetchall()
    
    stocks = []
    for row in rows:
        code = row['code']
        name = row['name']
        try:
            count_cursor = conn.execute(f'SELECT COUNT(*) as cnt FROM stock_{code}')
            count = count_cursor.fetchone()['cnt']
            if count > 0:
                stocks.append({'code': code, 'name': name})
        except:
            pass
    
    conn.close()
    return jsonify(stocks)

@app.route('/api/data/<stock_code>')
def get_data(stock_code):
    conn = get_db()
    table_name = f'stock_{stock_code}'
    try:
        cursor = conn.execute(f'SELECT * FROM {table_name} ORDER BY 日期')
        rows = cursor.fetchall()
        # 過濾掉收盤價為 None 的資料
        data = [dict(row) for row in rows if row['收盤價'] is not None]
        
        # 計算移動平均線
        for i in range(len(data)):
            # 5日移動平均
            if i >= 4:
                ma5 = sum(data[j]['收盤價'] for j in range(i-4, i+1)) / 5
                data[i]['MA5'] = round(ma5, 2)
            
            # 10日移動平均
            if i >= 9:
                ma10 = sum(data[j]['收盤價'] for j in range(i-9, i+1)) / 10
                data[i]['MA10'] = round(ma10, 2)
            
            # 20日移動平均
            if i >= 19:
                ma20 = sum(data[j]['收盤價'] for j in range(i-19, i+1)) / 20
                data[i]['MA20'] = round(ma20, 2)
                
    except:
        data = []
    conn.close()
    return jsonify(data)

@app.route('/api/backtest/<stock_code>')
def backtest(stock_code):
    from backtest import run_backtest_v2
    import json
    
    buy_strategies = json.loads(request.args.get('buy_strategies', '[]'))
    sell_strategies = json.loads(request.args.get('sell_strategies', '[]'))
    initial_capital = int(request.args.get('initial_capital', 1000000))
    
    try:
        result, df = run_backtest_v2(stock_code, buy_strategies, sell_strategies, initial_capital)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
