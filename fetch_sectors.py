"""
族群管理程式 - 最終版本
功能：
1. 從 CMoney 撈取股票族群資訊
2. 自動分為兩層結構（第一層：電子上游/傳產等，第二層：IC-代工/塑膠等）
3. 沒有族群的股票自動設為「其他」
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
import time
import warnings
import sys
import io
warnings.filterwarnings('ignore')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fetch_stock_sector(stock_id):
    """從 CMoney 撈取個股族群資訊"""
    url = f'https://www.cmoney.tw/forum/stock/{stock_id}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        sectors = soup.find_all('a', class_='link stockData__tag stockData__tag--category')
        return [s.get_text(strip=True) for s in sectors]
    except Exception as e:
        print(f'  錯誤: {e}')
        return []

def split_sector_to_levels(sector_name):
    """將族群名稱分為兩層"""
    if '-' in sector_name:
        parts = sector_name.split('-')
        level1 = parts[0].strip()
        level2 = '-'.join(parts[1:]).strip() if len(parts) > 1 else ''
    else:
        level1 = sector_name
        level2 = ''
    return level1, level2

def init_database():
    """初始化資料庫結構"""
    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    
    # 建立兩層族群表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_sector (
            stock_id TEXT,
            sector_level1 TEXT,
            sector_level2 TEXT,
            PRIMARY KEY (stock_id, sector_level1, sector_level2)
        )
    ''')
    
    conn.commit()
    conn.close()

def fetch_all_sectors():
    """撈取所有股票的族群資訊"""
    # 讀取股票清單
    df = pd.read_csv('stock_list.csv', encoding='utf-8-sig')
    stock_list = df['code'].astype(str).tolist()
    
    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    
    # 清空舊資料
    cursor.execute('DELETE FROM stock_sector')
    
    print(f'開始撈取 {len(stock_list)} 支股票的族群資訊...\n')
    
    success_count = 0
    fail_count = 0
    
    for i, stock_id in enumerate(stock_list, 1):
        print(f'[{i}/{len(stock_list)}] {stock_id}', end=' ', flush=True)
        
        sectors = fetch_stock_sector(stock_id)
        
        if sectors:
            for sector in sectors:
                level1, level2 = split_sector_to_levels(sector)
                cursor.execute(
                    'INSERT INTO stock_sector (stock_id, sector_level1, sector_level2) VALUES (?, ?, ?)',
                    (stock_id, level1, level2)
                )
            print(f'✓ {sectors[0]}', flush=True)
            success_count += 1
        else:
            # 沒有族群就設為「其他」
            cursor.execute(
                'INSERT INTO stock_sector (stock_id, sector_level1, sector_level2) VALUES (?, ?, ?)',
                (stock_id, '其他', '')
            )
            print('✗ 其他', flush=True)
            fail_count += 1
        
        conn.commit()
        time.sleep(1)  # 避免請求過快
    
    conn.close()
    print(f'\n完成！成功: {success_count}, 失敗: {fail_count}')

def update_missing_sectors():
    """只更新沒有族群或族群異常的股票"""
    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    
    # 從 stock_list 表取得所有股票
    cursor.execute('SELECT code FROM stock_list')
    all_stocks = set(row[0] for row in cursor.fetchall())
    
    # 找出已有有效族群的股票（sector_level1 不為空且不是「其他」）
    cursor.execute("SELECT DISTINCT stock_id FROM stock_sector WHERE sector_level1 != '' AND sector_level1 IS NOT NULL")
    stocks_with_valid_sector = set(row[0] for row in cursor.fetchall())
    
    # 找出需要更新的股票（完全沒有或只有「其他」）
    missing = all_stocks - stocks_with_valid_sector
    
    if not missing:
        print('所有股票都已有有效族群資訊')
        conn.close()
        return
    
    print(f'找到 {len(missing)} 支需要更新族群的股票\n')
    
    for i, stock_id in enumerate(sorted(missing), 1):
        print(f'[{i}/{len(missing)}] {stock_id}...', end=' ', flush=True)
        
        # 先刪除舊資料
        cursor.execute('DELETE FROM stock_sector WHERE stock_id = ?', (stock_id,))
        
        sectors = fetch_stock_sector(stock_id)
        
        if sectors:
            for sector in sectors:
                level1, level2 = split_sector_to_levels(sector)
                cursor.execute(
                    'INSERT INTO stock_sector (stock_id, sector_level1, sector_level2) VALUES (?, ?, ?)',
                    (stock_id, level1, level2)
                )
            print(f'✓ {sectors[0]}', flush=True)
        else:
            cursor.execute(
                'INSERT INTO stock_sector (stock_id, sector_level1, sector_level2) VALUES (?, ?, ?)',
                (stock_id, '其他', '')
            )
            print('✗ 其他', flush=True)
        
        conn.commit()
        time.sleep(1)
    
    conn.close()
    print('\n完成！')

if __name__ == '__main__':
    print('=== 族群管理程式 ===\n')
    
    # 初始化資料庫結構
    init_database()
    
    # 自動判斷：檢查是否有缺漏的族群
    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT code FROM stock_list')
    all_stocks = set(row[0] for row in cursor.fetchall())
    
    cursor.execute("SELECT DISTINCT stock_id FROM stock_sector WHERE sector_level1 != '' AND sector_level1 IS NOT NULL")
    stocks_with_valid_sector = set(row[0] for row in cursor.fetchall())
    
    missing = all_stocks - stocks_with_valid_sector
    conn.close()
    
    if missing:
        print(f'發現 {len(missing)} 支股票需要更新族群資訊')
        print('開始更新...\n')
        update_missing_sectors()
    else:
        print('所有股票都已有有效族群資訊！')
