import sqlite3
from FinMind.data import DataLoader
import os
from dotenv import load_dotenv

load_dotenv()
api = DataLoader()
api.login_by_token(api_token=os.getenv('Finmind_token'))

# 撈取台積電最近的三大法人資料
df = api.taiwan_stock_institutional_investors(stock_id='2330', start_date='2024-12-01')
print(f'撈取到 {len(df)} 筆三大法人資料')
print('欄位名稱:', df.columns.tolist())
print('\n前5筆:')
print(df.head(5))

# 檢查資料庫
conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

test_date = '2024-12-02'
cursor.execute(f'SELECT 日期, 外資買賣超 FROM stock_2330 WHERE 日期 = ?', (test_date,))
result = cursor.fetchone()
print(f'\n資料庫中 {test_date} 的資料: {result}')

conn.close()
