import sqlite3
import os

os.chdir('..')

conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

print("檢查穩懋(3105)資料")
print("=" * 80)

# 檢查 stock_list
cursor.execute("SELECT * FROM stock_list WHERE code = '3105'")
stock = cursor.fetchone()

if stock:
    print(f"stock_list 中找到: {stock[0]} {stock[1]}")
else:
    print("stock_list 中未找到 3105")

# 檢查資料表
print(f"\n檢查 stock_3105 資料表:")
try:
    cursor.execute("SELECT COUNT(*) FROM stock_3105")
    count = cursor.fetchone()[0]
    print(f"  資料筆數: {count}")
    
    if count > 0:
        cursor.execute("SELECT MIN(日期), MAX(日期) FROM stock_3105")
        min_date, max_date = cursor.fetchone()
        print(f"  日期範圍: {min_date} ~ {max_date}")
        
        # 顯示最近5筆
        cursor.execute("SELECT * FROM stock_3105 ORDER BY 日期 DESC LIMIT 5")
        rows = cursor.fetchall()
        print(f"\n  最近5筆資料:")
        for row in rows:
            print(f"    {row[0]}: 收盤價={row[4]}")
    else:
        print("  資料表是空的")
        
except Exception as e:
    print(f"  錯誤: {e}")

conn.close()
