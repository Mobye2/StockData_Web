import sqlite3
import pandas as pd
import sys
sys.path.append('..')

# 查詢2024-08-30前後的資料
conn = sqlite3.connect('../stock.db')
query = """
SELECT 日期, 收盤價
FROM stock_2308 
WHERE 日期 BETWEEN '2024-08-01' AND '2024-09-05'
ORDER BY 日期
"""
df = pd.read_sql_query(query, conn)
conn.close()

# 計算MA20
df['MA20'] = df['收盤價'].rolling(window=20).mean()
df['MA20_slope'] = df['MA20'].diff()

print("2024-08-30 前後的資料:")
print("=" * 80)
print(df[['日期', '收盤價', 'MA20', 'MA20_slope']].to_string(index=False))

# 重點檢查8/30
print("\n" + "=" * 80)
print("第一筆交易 2024-08-30 詳細檢查:")
print("=" * 80)
target_date = '2024-08-30'
idx = df[df['日期'] == target_date].index[0]

print(f"\n當天 {target_date}:")
print(f"  收盤價: {df.iloc[idx]['收盤價']:.2f}")
print(f"  MA20: {df.iloc[idx]['MA20']:.2f}")
print(f"  MA20斜率: {df.iloc[idx]['MA20_slope']:.4f}")

print(f"\n前一天 {df.iloc[idx-1]['日期']}:")
print(f"  MA20: {df.iloc[idx-1]['MA20']:.2f}")

print(f"\n斜率計算: {df.iloc[idx]['MA20']:.2f} - {df.iloc[idx-1]['MA20']:.2f} = {df.iloc[idx]['MA20_slope']:.4f}")
print(f"閾值: 30 / 100 = 0.3000")
print(f"斜率 > 閾值? {df.iloc[idx]['MA20_slope']:.4f} > 0.3000 = {df.iloc[idx]['MA20_slope'] > 0.3}")
