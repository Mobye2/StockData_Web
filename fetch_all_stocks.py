from FinMind.data import DataLoader
import sqlite3
import pandas as pd
import time
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
api = DataLoader()
api.login_by_token(api_token=os.getenv('Finmind_token'))

# 從CSV讀取股票清單
df_list = pd.read_csv('stock_list.csv', dtype={'code': str})
# 過濾：只保留純數字代碼（股票），排除ETF(00開頭)、權證(O結尾)等
df_list = df_list[df_list['code'].str.match(r'^[1-9]\d{3}$')]
STOCK_LIST = df_list.to_dict('records')

conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

# 建立股票清單表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_list (
        code TEXT PRIMARY KEY,
        name TEXT
    )
''')

# 插入股票清單
for stock in STOCK_LIST:
    cursor.execute('INSERT OR REPLACE INTO stock_list VALUES (?, ?)', 
                   (stock['code'], stock['name']))

conn.commit()

# 抓取每支股票資料
for stock_info in STOCK_LIST:
    code = str(stock_info['code'])
    name = stock_info['name']
    
    print(f"正在抓取 {code} {name}...", flush=True)
    
    try:
        table_name = f'stock_{code}'
        
        # 建立資料表（擴展籌碼欄位）
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                日期 TEXT PRIMARY KEY,
                開盤價 REAL,
                最高價 REAL,
                最低價 REAL,
                收盤價 REAL,
                成交量 INTEGER,
                成交金額 INTEGER,
                漲跌 REAL,
                成交筆數 INTEGER,
                融資買進 INTEGER,
                融資賣出 INTEGER,
                融券買進 INTEGER,
                融券賣出 INTEGER,
                外資買賣超 INTEGER,
                投信買賣超 INTEGER,
                自營商買賣超 INTEGER,
                外資持股比 REAL
            )
        ''')
        
        # 查詢最後一筆資料日期
        cursor.execute(f"SELECT MAX(日期) FROM {table_name}")
        last_date = cursor.fetchone()[0]
        
        # 判斷是否需要更新
        now = datetime.now()
        if now.hour >= 20:
            target_date = now.date()
        else:
            target_date = (now - timedelta(days=1)).date()
        
        if last_date:
            last_dt = datetime.strptime(last_date, '%Y-%m-%d')
            if last_dt.date() >= target_date:
                print(f"  最後資料: {last_date}，已是最新，跳過", flush=True)
                continue
            start_date = (last_dt + timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"  更新從 {start_date}...", flush=True)
        else:
            start_date = '2021-01-01'
            print(f"  第一次抓取 ({start_date})...", flush=True)
        
        print(f"  正在呼叫 FinMind API...", flush=True)
        df = api.taiwan_stock_daily(
            stock_id=code,
            start_date=start_date,
            end_date=target_date.strftime('%Y-%m-%d')
        )
        print(f"  API 回應完成", flush=True)
        
        # 檢查是否有資料
        if df is None or len(df) == 0:
            print(f"[SKIP] {code} {name} 無資料（可能已下市或暫停交易）", flush=True)
            continue
        
        print(f"  得到 {len(df)} 筆資料", flush=True)
        
        # 插入資料
        inserted = 0
        for _, row in df.iterrows():
            cursor.execute(f'''
                INSERT OR REPLACE INTO {table_name} 
                (日期, 開盤價, 最高價, 最低價, 收盤價, 成交量, 成交金額, 漲跌, 成交筆數)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['date'],
                row['open'], row['max'], row['min'], row['close'],
                row['Trading_Volume'], row['Trading_money'], row['spread'], row['Trading_turnover']
            ))
            inserted += 1
        
        conn.commit()
        print(f"[OK] {code} {name} 完成，新增/更新 {inserted} 筆", flush=True)
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n使用者中斷", flush=True)
        conn.commit()
        conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"[FAIL] {code} {name}: {e}", flush=True)
        conn.commit()
        continue

conn.close()
print("\n全部完成！")
