import sqlite3
import os

os.chdir('..')

conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

print("=" * 80)
print("鴻海(2317)股票資料")
print("=" * 80)

# 查詢資料筆數
cursor.execute("SELECT COUNT(*) FROM stock_2317")
count = cursor.fetchone()[0]
print(f"\n總資料筆數: {count}")

# 查詢日期範圍
cursor.execute("SELECT MIN(日期), MAX(日期) FROM stock_2317")
min_date, max_date = cursor.fetchone()
print(f"日期範圍: {min_date} ~ {max_date}")

# 顯示最近10筆資料
print(f"\n最近10筆資料:")
print("=" * 80)
cursor.execute("SELECT * FROM stock_2317 ORDER BY 日期 DESC LIMIT 10")
rows = cursor.fetchall()

print(f"{'日期':<12} {'開盤價':>8} {'最高價':>8} {'最低價':>8} {'收盤價':>8} {'成交量':>12}")
print("-" * 80)
for row in rows:
    print(f"{row[0]:<12} {row[1]:>8.2f} {row[2]:>8.2f} {row[3]:>8.2f} {row[4]:>8.2f} {row[5]:>12,}")

# 顯示最早10筆資料
print(f"\n最早10筆資料:")
print("=" * 80)
cursor.execute("SELECT * FROM stock_2317 ORDER BY 日期 ASC LIMIT 10")
rows = cursor.fetchall()

print(f"{'日期':<12} {'開盤價':>8} {'最高價':>8} {'最低價':>8} {'收盤價':>8} {'成交量':>12}")
print("-" * 80)
for row in rows:
    print(f"{row[0]:<12} {row[1]:>8.2f} {row[2]:>8.2f} {row[3]:>8.2f} {row[4]:>8.2f} {row[5]:>12,}")

# 統計資訊
cursor.execute("SELECT AVG(收盤價), MIN(收盤價), MAX(收盤價) FROM stock_2317")
avg_price, min_price, max_price = cursor.fetchone()

print(f"\n統計資訊:")
print("=" * 80)
print(f"平均收盤價: {avg_price:.2f}")
print(f"最低收盤價: {min_price:.2f}")
print(f"最高收盤價: {max_price:.2f}")

conn.close()
