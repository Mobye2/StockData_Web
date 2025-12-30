from flask import Flask, render_template, jsonify, request
import sqlite3
import subprocess
import threading
import atexit
import os
import signal

app = Flask(__name__)

# MCP Server 進程
mcp_process = None

def start_mcp_server():
    """啟動MCP Server"""
    global mcp_process
    try:
        mcp_process = subprocess.Popen(
            ['python', 'mcp_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        print(f"MCP Server 已啟動，PID: {mcp_process.pid}")
    except Exception as e:
        print(f"啟動MCP Server失敗: {e}")

def stop_mcp_server():
    """停止MCP Server"""
    global mcp_process
    if mcp_process:
        try:
            mcp_process.terminate()
            mcp_process.wait(timeout=5)
            print("MCP Server 已停止")
        except:
            mcp_process.kill()
            print("MCP Server 已強制停止")

# 註冊退出處理
atexit.register(stop_mcp_server)

def get_db():
    import os
    # 強制使用根目錄的資料庫
    db_path = os.path.join(os.path.dirname(__file__), '..', 'stock.db')
    conn = sqlite3.connect(db_path)
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
        
        # 計算移動平均線和其他技術指標
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
            
            # 確保三大法人資料存在（如果沒有則設為0）
            if '外資買賣超' not in data[i] or data[i]['外資買賣超'] is None:
                data[i]['外資買賣超'] = 0
            if '投信買賣超' not in data[i] or data[i]['投信買賣超'] is None:
                data[i]['投信買賣超'] = 0
            if '自營商買賣超' not in data[i] or data[i]['自營商買賣超'] is None:
                data[i]['自營商買賣超'] = 0
            if '外資持股比' not in data[i] or data[i]['外資持股比'] is None:
                data[i]['外資持股比'] = 0
                
    except Exception as e:
        print(f"Error loading data for {stock_code}: {e}")
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

# 儲存聊天歷史的全域變數
chat_sessions = {}

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    import json
    import os
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    from dotenv import load_dotenv
    import uuid
    from ai_tools import AVAILABLE_TOOLS, execute_tool
    
    print("DEBUG: AI聊天API被調用")
    
    load_dotenv(override=True)
    
    data = request.json
    print(f"DEBUG: 收到請求資料: {data}")
    session_id = data.get('session_id')
    user_message = data.get('message', '')
    
    # 如果沒有session_id，創建新的聊天會話
    if not session_id:
        session_id = str(uuid.uuid4())
        chat_sessions[session_id] = []
    
    # 如果是新會話且包含回測資料，初始化系統提示
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    
    # 檢查是否包含回測資料（首次分析）
    stock_code = data.get('stock_code')
    if stock_code and len(chat_sessions[session_id]) == 0:
        # 首次分析
        stock_name = data.get('stock_name')
        sector = data.get('sector', '')
        buy_strategies = data.get('buy_strategies', [])
        sell_strategies = data.get('sell_strategies', [])
        backtest_result = data.get('backtest_result', {})
        
        # 生成表格格式的交易明細
        trades = backtest_result.get('trades', [])
        sell_trades = [t for t in trades if t.get('類型') == '賣出']
        
        trade_table = "#\t買入日期\t買入策略\t買入價\t賣出日期\t賣出策略\t賣出價\t數量\t獲利\t報酬率\t賣出原因\n"
        
        for i, trade in enumerate(sell_trades, 1):
            buy_records = trade.get('買入記錄', [])
            if buy_records:
                buy_date = buy_records[0]['日期']
                avg_buy_price = sum(r['價格'] * r['數量'] for r in buy_records) / trade['數量']
            else:
                buy_date = 'N/A'
                avg_buy_price = 0
            
            # 找到對應的買入交易來獲取策略編號
            buy_trade = next((t for t in trades if t.get('類型') == '買入' and 
                            any(r['日期'] == t['日期'] for r in buy_records)), None)
            buy_strategy = ','.join(map(str, buy_trade.get('策略編號', ['-']))) if buy_trade else '-'
            sell_strategy = ','.join(map(str, trade.get('策略編號', ['-'])))
            
            trade_table += f"{i}\t{buy_date}\t{buy_strategy}\t{avg_buy_price:.2f}\t{trade['日期']}\t{sell_strategy}\t{trade['價格']:.2f}\t{trade['數量']:,}\t{trade.get('獲利', 0):,}\t{trade.get('報酬率', 0):.2f}%\t{trade.get('賣出原因', '策略信號')}\n"
        
        # 格式化策略信息
        def format_strategies(strategies, strategy_type):
            if not strategies:
                return f"無{strategy_type}策略"
            
            strategy_text = ""
            for i, strategy in enumerate(strategies, 1):
                strategy_text += f"  策略{i}："
                indicators = strategy.get('indicators', [])
                if indicators:
                    indicator_names = []
                    for ind in indicators:
                        ind_type = ind.get('type', '')
                        params = ind.get('params', {})
                        if ind_type == 'ma_crossover':
                            indicator_names.append(f"均線交叉({params.get('short_window', 5)}/{params.get('long_window', 20)})")
                        elif ind_type == 'ma_above':
                            ma_period = params.get('ma_period', 20)
                            indicator_names.append(f"超過{ma_period}日均線")
                        elif ind_type == 'ma_below':
                            ma_period = params.get('ma_period', 20)
                            indicator_names.append(f"跌破{ma_period}日均線")
                        elif ind_type == 'rsi':
                            threshold = params.get('buy_threshold' if strategy_type == '買進' else 'sell_threshold', 30)
                            indicator_names.append(f"RSI({threshold})")
                        elif ind_type == 'take_profit':
                            indicator_names.append(f"停利({params.get('profit_pct', 10)}%)")
                        elif ind_type == 'stop_loss':
                            indicator_names.append(f"停損({params.get('loss_pct', -10)}%)")
                        elif ind_type == 'high_volume':
                            indicator_names.append(f"大量({params.get('volume_multiplier', 2)}倍)")
                        elif ind_type == 'ma_slope_up':
                            indicator_names.append(f"均線上升({params.get('threshold', 10)}%)")
                        elif ind_type == 'ma_slope_down':
                            indicator_names.append(f"均線下降({params.get('threshold', -10)}%)")
                        elif ind_type == 'w_bottom':
                            indicator_names.append(f"W底突破(回看{params.get('lookback', 60)}日)")
                        elif ind_type == 'ma_above':
                            ma_period = params.get('ma_period', 20)
                            indicator_names.append(f"超過{ma_period}日均線")
                        elif ind_type == 'ma_below':
                            ma_period = params.get('ma_period', 20)
                            indicator_names.append(f"跌破{ma_period}日均線")
                        else:
                            indicator_names.append(ind_type)
                    strategy_text += " + ".join(indicator_names)
                else:
                    strategy_text += "未設定指標"
                strategy_text += "\n"
            return strategy_text.strip()
        
        buy_strategy_text = format_strategies(buy_strategies, '買進')
        sell_strategy_text = format_strategies(sell_strategies, '賣出')
        
        initial_prompt = f"""請分析以下台股回測結果：

## 股票資訊
{stock_code} {stock_name} ({sector})

## 交易策略
### 買進策略：
{buy_strategy_text}

### 賣出策略：
{sell_strategy_text}

## 績效摘要
- 總報酬率：{backtest_result.get('return_rate', 0):.2f}%
- 總獲利：{backtest_result.get('profit', 0):,}元
- 交易次數：{backtest_result.get('total_trades', 0)}次
- 勝率：{backtest_result.get('win_rate', 0):.2f}%

## 交易明細
{trade_table}
請分析策略表現並提供改進建議。如需K棒資料可使用工具查詢。"""
        
        print("=" * 80)
        print("DEBUG: 發送給LLM的初始提示:")
        print(initial_prompt)
        print("=" * 80)
        
        chat_sessions[session_id].append({
            'role': 'user',
            'content': initial_prompt
        })
    else:
        # 後續對話
        chat_sessions[session_id].append({
            'role': 'user',
            'content': user_message
        })
    
    # 系統提示詞
    system_prompt = """你是一位資深的量化交易分析師，具備以下專業能力：

1. **技術分析專家**：精通各種技術指標及其組合應用
2. **策略優化師**：擅長分析交易策略的優缺點，提供具體優化建議
3. **風險管理專家**：深度理解風險控制和資金管理原則
4. **台灣股市專家**：熟悉台灣股市特性環境

請針對買進與賣出策略給予建議，分析內容請確保數據支撐。如果使用者提出K棒資訊，可使用工具查詢。"""
        
    try:
        api_key = os.getenv('BEDROCK_API_KEY')
        
        if not api_key:
            return jsonify({'error': 'API Key未設定'}), 500
        
        # 工具調用循環（最多5次）
        for iteration in range(5):
            print(f"DEBUG: 迭代 {iteration + 1}")
            
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "system": system_prompt,
                "messages": chat_sessions[session_id],
                "tools": AVAILABLE_TOOLS
            }
            
            print(f"DEBUG: 發送給LLM的完整payload:")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            print("=" * 80)
            
            req = Request(
                'https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-sonnet-4-20250514-v1:0/invoke',
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                }
            )
            
            with urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # 將 AI 回應加入歷史
                chat_sessions[session_id].append({
                    'role': 'assistant',
                    'content': result['content']
                })
                
                # 檢查是否需要調用工具
                if result.get('stop_reason') == 'tool_use':
                    print("DEBUG: AI 要求調用工具")
                    
                    # 執行所有工具調用
                    tool_results = []
                    for content in result['content']:
                        if content['type'] == 'tool_use':
                            tool_name = content['name']
                            tool_input = content['input']
                            tool_id = content['id']
                            
                            print(f"DEBUG: 執行工具 {tool_name}")
                            tool_result = execute_tool(tool_name, tool_input)
                            
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": tool_result
                            })
                    
                    # 將工具結果加入歷史
                    chat_sessions[session_id].append({
                        'role': 'user',
                        'content': tool_results
                    })
                    
                    # 繼續下一輪循環
                    continue
                else:
                    # AI 完成回答
                    ai_response = ''
                    for content in result['content']:
                        if content['type'] == 'text':
                            ai_response += content['text']
                    
                    return jsonify({
                        'session_id': session_id,
                        'response': ai_response,
                        'chat_history': chat_sessions[session_id]
                    })
        
        # 如果超過最大迭代次數
        return jsonify({'error': '工具調用超過最大次數'}), 500
            
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"DEBUG: HTTP錯誤 - {e.code}: {error_body}")
        return jsonify({'error': f'API請求失敗: {e.code}'}), 500
    except Exception as e:
        print(f"DEBUG: 錯誤 - {str(e)}")
        return jsonify({'error': f'AI分析失敗: {str(e)}'}), 500

# @app.route('/api/ai-chat-with-mcp', methods=['POST'])
# def ai_chat_with_mcp():
#     import json
#     import os
#     import asyncio
#     from urllib.request import Request, urlopen
#     from urllib.error import HTTPError, URLError
#     from dotenv import load_dotenv
#     import uuid
#     from mcp_agent import analyze_with_mcp_tools
#     
#     load_dotenv(override=True)
#     
#     data = request.json
#     session_id = data.get('session_id')
#     user_message = data.get('message', '')
#     
#     if not session_id:
#         session_id = str(uuid.uuid4())
#         chat_sessions[session_id] = []
#     
#     if session_id not in chat_sessions:
#         chat_sessions[session_id] = []
#     
#     # 檢查是否包含回測資料（首次分析）
#     stock_code = data.get('stock_code')
#     if stock_code and len(chat_sessions[session_id]) == 0:
#         # 使用MCP Agent分析回測結果
#         backtest_result = data.get('backtest_result', {})
#         
#         try:
#             # 使用MCP工具獲取市場資料
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
#             mcp_analysis = loop.run_until_complete(
#                 analyze_with_mcp_tools(backtest_result, stock_code)
#             )
#             loop.close()
#         except Exception as e:
#             mcp_analysis = {"error": f"MCP分析失敗: {str(e)}"}
#         
#         # 組織包含MCP分析結果的提示
#         stock_name = data.get('stock_name')
#         sector = data.get('sector', '')
#         buy_strategies = data.get('buy_strategies', [])
#         sell_strategies = data.get('sell_strategies', [])
#         
#         initial_prompt = f"""請對以下台股回測結果進行深度分析：
# 
# ## 股票資訊
# - **代碼**：{stock_code}
# - **名稱**：{stock_name}
# - **族群**：{sector}
# 
# ## 交易策略設定
# ### 買進策略：
# {json.dumps(buy_strategies, ensure_ascii=False, indent=2)}
# 
# ### 賣出策略：
# {json.dumps(sell_strategies, ensure_ascii=False, indent=2)}
# 
# ## 回測績效結果
# - **總報酬率**：{backtest_result.get('return_rate', 0):.2f}%
# - **總獲利**：{backtest_result.get('profit', 0):,} 元
# - **交易次數**：{backtest_result.get('total_trades', 0)} 次
# - **勝率**：{backtest_result.get('win_rate', 0):.2f}%
# 
# ## MCP工具分析結果
# {json.dumps(mcp_analysis, ensure_ascii=False, indent=2)}
# 
# 請基於以上回測結果和市場環境資料，提供策略分析和優化建議。"""
#         
#         chat_sessions[session_id].append({
#             'role': 'user',
#             'content': initial_prompt
#         })
#     else:
#         chat_sessions[session_id].append({
#             'role': 'user',
#             'content': user_message
#         })
#     
#     # 系統提示詞
#     system_prompt = """你是一位資深的量化交易分析師，具備以下專業能力：
# 
# 1. **技術分析專家**：精通各種技術指標及其組合應用
# 2. **策略優化師**：擅長分析交易策略的優缺點，提供具體優化建議
# 3. **風險管理專家**：深度理解風險控制和資金管理原則
# 4. **台灣股市專家**：熟悉台灣股市特性環境
# 
# **回答風格**：專業、精確、實用，使用數據支持的分析結論。可以進行多輪對話，回答用戶的後續問題。"""
#     
#     try:
#         api_key = os.getenv('BEDROCK_API_KEY')
#         
#         if not api_key:
#             return jsonify({'error': 'API Key未設定，請在.env檔案中設定BEDROCK_API_KEY'}), 500
#         
#         payload = {
#             "anthropic_version": "bedrock-2023-05-31",
#             "max_tokens": 1500,
#             "system": system_prompt,
#             "messages": chat_sessions[session_id]
#         }
#         
#         req = Request(
#             'https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-sonnet-4-20250514-v1:0/invoke',
#             data=json.dumps(payload).encode('utf-8'),
#             headers={
#                 'Content-Type': 'application/json',
#                 'Authorization': f'Bearer {api_key}'
#             }
#         )
#         
#         with urlopen(req, timeout=60) as response:
#             result = json.loads(response.read().decode('utf-8'))
#             ai_response = result['content'][0]['text']
#             
#             chat_sessions[session_id].append({
#                 'role': 'assistant',
#                 'content': ai_response
#             })
#             
#             return jsonify({
#                 'session_id': session_id,
#                 'response': ai_response,
#                 'chat_history': chat_sessions[session_id]
#             })
#             
#     except Exception as e:
#         return jsonify({'error': f'AI分析失敗: {str(e)}'}), 500

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    import json
    import os
    
    strategies_file = '../strategies.json' if os.path.exists('../strategies.json') else 'strategies.json'
    if not os.path.exists(strategies_file):
        return jsonify({'buy_strategies': [], 'sell_strategies': []})
    
    try:
        with open(strategies_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategies', methods=['POST'])
def save_strategy():
    import json
    import os
    
    data = request.json
    strategy_type = data.get('type')  # 'buy' or 'sell'
    name = data.get('name')
    strategies = data.get('strategies')
    
    if not all([strategy_type, name, strategies]):
        return jsonify({'error': '缺少必要參數'}), 400
    
    strategies_file = '../strategies.json' if os.path.exists('../strategies.json') else 'strategies.json'
    
    # 載入現有策略
    if os.path.exists(strategies_file):
        try:
            with open(strategies_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
        except:
            saved_data = {'buy_strategies': [], 'sell_strategies': []}
    else:
        saved_data = {'buy_strategies': [], 'sell_strategies': []}
    
    # 添加新策略
    strategy_entry = {'name': name, 'strategies': strategies}
    
    if strategy_type == 'buy':
        saved_data['buy_strategies'].append(strategy_entry)
    elif strategy_type == 'sell':
        saved_data['sell_strategies'].append(strategy_entry)
    else:
        return jsonify({'error': '無效的策略類型'}), 400
    
    # 儲存到檔案
    try:
        with open(strategies_file, 'w', encoding='utf-8') as f:
            json.dump(saved_data, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True, 'message': '策略已儲存'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategies/<strategy_type>/<int:index>', methods=['DELETE'])
def delete_strategy(strategy_type, index):
    import json
    import os
    
    strategies_file = '../strategies.json' if os.path.exists('../strategies.json') else 'strategies.json'
    if not os.path.exists(strategies_file):
        return jsonify({'error': '策略檔案不存在'}), 404
    
    try:
        with open(strategies_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        if strategy_type == 'buy':
            if 0 <= index < len(saved_data['buy_strategies']):
                saved_data['buy_strategies'].pop(index)
            else:
                return jsonify({'error': '策略索引無效'}), 400
        elif strategy_type == 'sell':
            if 0 <= index < len(saved_data['sell_strategies']):
                saved_data['sell_strategies'].pop(index)
            else:
                return jsonify({'error': '策略索引無效'}), 400
        else:
            return jsonify({'error': '無效的策略類型'}), 400
        
        with open(strategies_file, 'w', encoding='utf-8') as f:
            json.dump(saved_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': '策略已刪除'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        # 檢查API Key是否存在（不顯示完整內容）
        print(f"DEBUG: API Key loaded: {'Yes' if api_key else 'No'} (Length: {len(api_key) if api_key else 0})")
        
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
            'https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-sonnet-4-20250514-v1:0/invoke',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
        )
        
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            message = result['content'][0]['text']
            return jsonify({'success': True, 'message': message, 'region': 'us-east-1'})
            
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        return jsonify({'success': False, 'error': f'API請求失敗: {e.code} - {error_body}'}), 500
    except URLError as e:
        return jsonify({'success': False, 'error': f'網路錯誤: {str(e.reason)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # 啟動MCP Server
    print("正在啟動MCP Server...")
    start_mcp_server()
    
    try:
        print("正在啟動Web服務...")
        app.run(debug=True, port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("正在關閉服務...")
    finally:
        stop_mcp_server()
