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

@app.route('/multi-backtest')
def multi_backtest_page():
    return render_template('multi_backtest.html', active_page='multi_backtest')

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

@app.route('/api/ai-analysis', methods=['POST'])
def ai_analysis():
    import json
    import os
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    from dotenv import load_dotenv
    
    load_dotenv()
    
    data = request.json
    stock_code = data.get('stock_code')
    stock_name = data.get('stock_name')
    sector = data.get('sector', '')
    buy_strategies = data.get('buy_strategies', [])
    sell_strategies = data.get('sell_strategies', [])
    backtest_result = data.get('backtest_result', {})
    stock_data = data.get('stock_data', [])
    
    # 組織提示詞
    prompt = f"""請分析以下台股回測結果：

股票資訊：
- 代碼：{stock_code}
- 名稱：{stock_name}
- 族群：{sector}

買進策略：
{json.dumps(buy_strategies, ensure_ascii=False, indent=2)}

賣出策略：
{json.dumps(sell_strategies, ensure_ascii=False, indent=2)}

回測結果：
- 報酬率：{backtest_result.get('return_rate', 0):.2f}%
- 獲利：{backtest_result.get('profit', 0):,}
- 交易次數：{backtest_result.get('total_trades', 0)}
- 勝率：{backtest_result.get('win_rate', 0):.2f}%
- 最大回撤：{backtest_result.get('max_drawdown', 0):.2f}%

交易明細：
{json.dumps(backtest_result.get('trades', [])[:10], ensure_ascii=False, indent=2)}

股票數據樣本（最近10筆）：
{json.dumps(stock_data[-10:] if len(stock_data) > 10 else stock_data, ensure_ascii=False, indent=2)}

請提供：
1. 策略表現分析
2. 優缺點評估
3. 改進建議
4. 風險提示
"""
    
    try:
        api_key = os.getenv('BEDROCK_API_KEY')
        
        if not api_key:
            return jsonify({'error': 'API Key未設定，請在.env檔案中設定BEDROCK_API_KEY'}), 500
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        req = Request(
            'https://bedrock-runtime.us-east-1.amazonaws.com/model/anthropic.claude-4-5-sonnet-20250929-v1:0/invoke',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
        )
        
        with urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            analysis = result['content'][0]['text']
            return jsonify({'analysis': analysis})
            
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        return jsonify({'error': f'API請求失敗: {e.code} - {error_body}'}), 500
    except URLError as e:
        return jsonify({'error': f'網路錯誤: {str(e.reason)}'}), 500
    except Exception as e:
        return jsonify({'error': f'AI分析失敗: {str(e)}'}), 500

@app.route('/api/test-ai', methods=['GET'])
def test_ai():
    import json
    import os
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    from dotenv import load_dotenv
    
    load_dotenv()
    
    try:
        api_key = os.getenv('BEDROCK_API_KEY')
        
        if not api_key:
            return jsonify({'error': 'API Key未設定，請在.env檔案中設定BEDROCK_API_KEY'}), 500
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello! Please respond with a simple greeting."
                }
            ]
        }
        
        req = Request(
            'https://bedrock-runtime.us-east-1.amazonaws.com/model/anthropic.claude-3-sonnet-20240229-v1:0/invoke',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
        )
        
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            message = result['content'][0]['text']
            return jsonify({'success': True, 'message': message})
            
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        return jsonify({'success': False, 'error': f'API請求失敗: {e.code} - {error_body}'}), 500
    except URLError as e:
        return jsonify({'success': False, 'error': f'網路錯誤: {str(e.reason)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
