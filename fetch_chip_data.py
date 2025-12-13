"""
從 FinMind 撈取籌碼資訊並更新到 stock_XXXX 表
"""

from FinMind.data import DataLoader
import sqlite3
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
api = DataLoader()
api.login_by_token(api_token=os.getenv('Finmind_token'))

def check_last_chip_date(stock_id):
    """檢查最後一筆籌碼資料日期"""
    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    table_name = f'stock_{stock_id}'
    
    try:
        cursor.execute(f'SELECT MAX(日期) FROM {table_name} WHERE 外資買賣超 IS NOT NULL')
        last_date = cursor.fetchone()[0]
    except:
        # 表格不存在或欄位不存在，返回None
        last_date = None
    
    conn.close()
    return last_date

def fetch_margin_data(stock_id, start_date='2021-01-01'):
    """撈取融資融券資料"""
    try:
        df = api.taiwan_stock_margin_purchase_short_sale(
            stock_id=stock_id,
            start_date=start_date
        )
        if df is not None and len(df) > 0:
            return df
    except Exception as e:
        print(f'  融資融券錯誤: {e}')
    return None

def fetch_institutional_data(stock_id, start_date='2021-01-01'):
    """撈取三大法人買賣資料"""
    try:
        df = api.taiwan_stock_institutional_investors(
            stock_id=stock_id,
            start_date=start_date
        )
        if df is not None and len(df) > 0:
            return df
    except Exception as e:
        print(f'  三大法人錯誤: {e}')
    return None

def fetch_foreign_holding(stock_id, start_date='2021-01-01'):
    """撈取外資持股比資料"""
    try:
        df = api.taiwan_stock_shareholding(
            stock_id=stock_id,
            start_date=start_date
        )
        if df is not None and len(df) > 0:
            return df
    except Exception as e:
        pass
    return None

def add_chip_columns(stock_id):
    """為舊表格新增籌碼欄位"""
    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    table_name = f'stock_{stock_id}'
    
    columns = [
        '融資買進 INTEGER',
        '融資賣出 INTEGER',
        '融券買進 INTEGER',
        '融券賣出 INTEGER',
        '外資買賣超 INTEGER',
        '投信買賣超 INTEGER',
        '自營商買賣超 INTEGER',
        '外資持股比 REAL'
    ]
    
    for col in columns:
        try:
            cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {col}')
        except:
            pass
    
    conn.commit()
    conn.close()

def save_chip_data(stock_id, margin_df, institutional_df, foreign_df):
    """更新 stock_XXXX 表的籌碼欄位"""
    add_chip_columns(stock_id)
    
    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    table_name = f'stock_{stock_id}'
    
    updated = 0
    
    if margin_df is not None and len(margin_df) > 0:
        for _, row in margin_df.iterrows():
            cursor.execute(f'''
                UPDATE {table_name} SET 
                融資買進 = ?, 融資賣出 = ?, 融券買進 = ?, 融券賣出 = ?
                WHERE 日期 = ?
            ''', (row.get('MarginPurchaseBuy', 0), row.get('MarginPurchaseSell', 0),
                  row.get('ShortSaleBuy', 0), row.get('ShortSaleSell', 0), row.get('date')))
            updated += cursor.rowcount
    
    if institutional_df is not None and len(institutional_df) > 0:
        for date in institutional_df['date'].unique():
            date_data = institutional_df[institutional_df['date'] == date]
            foreign = date_data[date_data['name'] == 'Foreign_Investor']
            trust = date_data[date_data['name'] == 'Investment_Trust']
            dealer_self = date_data[date_data['name'] == 'Dealer_self']
            
            foreign_net = int(foreign['buy'].iloc[0] - foreign['sell'].iloc[0]) if len(foreign) > 0 else 0
            trust_net = int(trust['buy'].iloc[0] - trust['sell'].iloc[0]) if len(trust) > 0 else 0
            dealer_net = int(dealer_self['buy'].iloc[0] - dealer_self['sell'].iloc[0]) if len(dealer_self) > 0 else 0
            
            cursor.execute(f'''
                UPDATE {table_name} SET 
                外資買賣超 = ?, 投信買賣超 = ?, 自營商買賣超 = ?
                WHERE 日期 = ?
            ''', (foreign_net, trust_net, dealer_net, date))
    
    if foreign_df is not None and len(foreign_df) > 0:
        for _, row in foreign_df.iterrows():
            value = row.get('ForeignInvestmentRemainRatio')
            if value is not None:
                cursor.execute(f'''
                    UPDATE {table_name} SET 外資持股比 = ?
                    WHERE 日期 = ?
                ''', (value, row.get('date')))
    
    conn.commit()
    conn.close()
    return updated

if __name__ == '__main__':
    print('=== 籌碼資料撈取程式 ===\n')
    
    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    cursor.execute('SELECT code, name FROM stock_list ORDER BY code')
    stocks = cursor.fetchall()
    conn.close()
    
    start_date = '2021-01-01'
    print(f'撈取期間: {start_date} ~ {datetime.now().strftime("%Y-%m-%d")}\n')
    print(f'開始撈取 {len(stocks)} 支股票的籌碼資料...\n')
    
    success = 0
    fail = 0
    
    for i, (stock_id, name) in enumerate(stocks, 1):
        print(f'[{i}/{len(stocks)}] {stock_id} {name}', flush=True)
        
        # 檢查最後一筆籌碼資料
        last_chip_date = check_last_chip_date(stock_id)
        now = datetime.now()
        target_date = now.date() if now.hour >= 20 else (now - timedelta(days=1)).date()
        
        # if last_chip_date:
        #     last_dt = datetime.strptime(last_chip_date, '%Y-%m-%d')
        #     if last_dt.date() >= target_date:
        #         print(f'  最後籌碼資料: {last_chip_date}，已是最新，跳過', flush=True)
        #         continue
        #     fetch_start = (last_dt + timedelta(days=1)).strftime('%Y-%m-%d')
        # else:
        fetch_start = start_date
        
        margin_df = fetch_margin_data(stock_id, fetch_start)
        institutional_df = fetch_institutional_data(stock_id, fetch_start)
        foreign_df = fetch_foreign_holding(stock_id, fetch_start)
        
        if margin_df is not None or institutional_df is not None or foreign_df is not None:
            try:
                updated = save_chip_data(stock_id, margin_df, institutional_df, foreign_df)
                inst_days = len(institutional_df['date'].unique()) if institutional_df is not None else 0
                print(f'  ✓ 融資融券:{len(margin_df) if margin_df is not None else 0} 三大法人:{inst_days}天 外資持股:{len(foreign_df) if foreign_df is not None else 0}', flush=True)
                success += 1
            except Exception as e:
                print(f'  ✗ 儲存失敗: {e}', flush=True)
                fail += 1
        else:
            print(f'  ✗ 無資料', flush=True)
            fail += 1
        
        time.sleep(1)
    
    print(f'\n完成！成功: {success}, 失敗: {fail}')
