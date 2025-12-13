import sqlite3
import os

os.chdir('..')

conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

# 查詢所有資料表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("資料庫中的股票資料表:")
print("=" * 60)

for table in tables:
    table_name = table[0]
    if table_name.startswith('stock_'):
        stock_code = table_name.replace('stock_', '')
        
        # 查詢該股票的資料筆數和日期範圍
        cursor.execute(f"SELECT COUNT(*), MIN(日期), MAX(日期) FROM {table_name}")
        count, min_date, max_date = cursor.fetchone()
        
        print(f"股票代碼: {stock_code}")
        print(f"  資料筆數: {count}")
        print(f"  日期範圍: {min_date} ~ {max_date}")
        print()

conn.close()

print("\n檢查鴻海(2317)是否存在:")
print("=" * 60)
conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

try:
    cursor.execute("SELECT COUNT(*) FROM stock_2317")
    count = cursor.fetchone()[0]
    print(f"鴻海(2317)資料筆數: {count}")
except Exception as e:
    print(f"鴻海(2317)不存在: {e}")

conn.close()
