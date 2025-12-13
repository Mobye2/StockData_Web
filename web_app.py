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
    return render_template('single_backtest.html', active_page='backtest')

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
    
    load_dotenv(override=True)
    
    data = request.json
    stock_code = data.get('stock_code')
    stock_name = data.get('stock_name')
    sector = data.get('sector', '')
    buy_strategies = data.get('buy_strategies', [])
    sell_strategies = data.get('sell_strategies', [])
    backtest_result = data.get('backtest_result', {})
    stock_data = data.get('stock_data', [])
    
    # 獲取每次交易前20日的數據
    trade_context_data = []
    if backtest_result.get('trades'):
        conn = get_db()
        try:
            # 獲取所有股票數據
            cursor = conn.execute(f'SELECT * FROM stock_{stock_code} ORDER BY 日期')
            all_data = [dict(row) for row in cursor.fetchall()]
            
            # 為每次交易提取前20日數據
            for trade in backtest_result.get('trades', []):
                trade_date = trade.get('日期')
                if trade_date:
                    # 找到交易日期的索引
                    trade_idx = next((i for i, d in enumerate(all_data) if d['日期'] == trade_date), None)
                    if trade_idx and trade_idx >= 20:
                        # 提取前20日數據
                        pre_trade_data = all_data[trade_idx-20:trade_idx]
                        trade_context_data.append({
                            '交易日期': trade_date,
                            '交易類型': trade.get('類型', ''),
                            '前20日數據': pre_trade_data
                        })
        except:
            trade_context_data = []
        finally:
            conn.close()
    
    # 組織系統提示詞（專業角色設定）
    system_prompt = """你是一位資深的量化交易分析師，具備以下專業能力：

1. **技術分析專家**：精通各種技術指標（MA、RSI、MACD等）及其組合應用
2. **策略優化師**：擅長分析交易策略的優缺點，提供具體優化建議
3. **風險管理專家**：深度理解風險控制和資金管理原則
4. **行為金融學家**：能夠分析交易者的行為模式和心理偏誤
5. **台灣股市專家**：熟悉台灣股市特性環境

**分析原則**：
- 優先目標：最大化總獲利（絕對金額）
- 次要目標：提升勝率和減少回撤
- 深度分析使用者的操作習慣和偏好
- 提供具體、可執行的優化建議

**回答風格**：專業、精確、實用，使用數據支持的分析結論。"""
    
    # 組織用戶提示詞
    user_prompt = f"""請對以下台股回測結果進行深度分析：

## 股票資訊
- **代碼**：{stock_code}
- **名稱**：{stock_name}
- **族群**：{sector}

## 交易策略設定
### 買進策略（任一達成即買進）：
{json.dumps(buy_strategies, ensure_ascii=False, indent=2)}

### 賣出策略（任一達成即賣出）：
{json.dumps(sell_strategies, ensure_ascii=False, indent=2)}

## 回測績效結果
- **總報酬率**：{backtest_result.get('return_rate', 0):.2f}%
- **總獲利**：{backtest_result.get('profit', 0):,} 元
- **交易次數**：{backtest_result.get('total_trades', 0)} 次
- **勝率**：{backtest_result.get('win_rate', 0):.2f}%
- **最大回撤**：{backtest_result.get('max_drawdown', 0):.2f}%
- **平均每筆獲利**：{backtest_result.get('profit', 0) / max(backtest_result.get('total_trades', 1), 1):,.0f} 元

## 詳細交易記錄
{json.dumps(backtest_result.get('trades', []), ensure_ascii=False, indent=2)}

## 每次交易前20日市場環境分析
{json.dumps(trade_context_data, ensure_ascii=False, indent=2)}

## 分析要求
請基於以上資料，提供以下分析：

### 1. 獲利最大化優化建議，
- **主要目標**：提升總獲利金額
- 建議新增或移除的指標組合
- 提供具體的參數調整建議
- 在不衝突下提供勝率提升策略

請以專業、數據化的方式進行分析，並提供具體可操作的建議。
直接針對策略指標或參數給予建議即可，請給予一個方案，用條列口語的方式表達"""
    

    
    try:
        api_key = os.getenv('BEDROCK_API_KEY')
        
        if not api_key:
            return jsonify({'error': 'API Key未設定，請在.env檔案中設定BEDROCK_API_KEY'}), 500
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        }
        
        req = Request(
            'https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-sonnet-4-5-20250929-v1:0/invoke',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
        )
        
        with urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            analysis = result['content'][0]['text']
            
            # 在 console 顯示 AI 回應
            print("=" * 80)
            print("AI RESPONSE:")
            print("=" * 80)
            print(analysis)
            print("=" * 80)
            
            return jsonify({
                'analysis': analysis,
                'user_prompt': user_prompt,
                'system_prompt': system_prompt
            })
            
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
    
    load_dotenv(override=True)
    
    try:
        api_key = os.getenv('BEDROCK_API_KEY')
        
        # 在測試AI功能中顯示TOKEN
        print(f"DEBUG: BEDROCK_API_KEY = {api_key}")
        
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
            'https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-sonnet-4-5-20250929-v1:0/invoke',
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
