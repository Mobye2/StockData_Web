import sqlite3
import os

os.chdir('..')

conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

print("檢查鴻海資料中的 None 值")
print("=" * 80)

cursor.execute("SELECT * FROM stock_2317 ORDER BY 日期")
rows = cursor.fetchall()

print(f"總共 {len(rows)} 筆資料\n")

# 檢查是否有 None 值
none_count = 0
for i, row in enumerate(rows):
    has_none = any(v is None for v in row)
    if has_none:
        none_count += 1
        if none_count <= 5:  # 只顯示前5筆
            print(f"第 {i+1} 筆有 None 值:")
            print(f"  日期: {row[0]}")
            print(f"  開盤價: {row[1]}")
            print(f"  最高價: {row[2]}")
            print(f"  最低價: {row[3]}")
            print(f"  收盤價: {row[4]}")
            print(f"  成交量: {row[5]}")
            print()

print(f"共有 {none_count} 筆資料包含 None 值")

conn.close()
