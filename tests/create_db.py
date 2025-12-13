import sqlite3
import pandas as pd

# 讀取CSV
df = pd.read_csv('台積電_2024_8_至今.csv')

# 建立SQLite資料庫
conn = sqlite3.connect('stock.db')

# 將資料寫入資料庫
df.to_sql('tsmc_daily', conn, if_exists='replace', index=False)

print(f"成功建立資料庫，共 {len(df)} 筆資料")
conn.close()
