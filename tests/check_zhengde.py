import sqlite3
import os

os.chdir('..')

conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

print("查詢正德相關股票")
print("=" * 80)

# 查詢 stock_list 中包含"正德"的股票
cursor.execute("SELECT * FROM stock_list WHERE name LIKE '%正德%'")
stocks = cursor.fetchall()

if stocks:
    print(f"找到 {len(stocks)} 支包含'正德'的股票:\n")
    for stock in stocks:
        code = stock[0]
        name = stock[1]
        print(f"代碼: {code}, 名稱: {name}")
        
        # 檢查資料筆數
        try:
            cursor.execute(f"SELECT COUNT(*) FROM stock_{code}")
            count = cursor.fetchone()[0]
            print(f"  資料筆數: {count}")
            
            if count > 0:
                cursor.execute(f"SELECT MIN(日期), MAX(日期) FROM stock_{code}")
                min_date, max_date = cursor.fetchone()
                print(f"  日期範圍: {min_date} ~ {max_date}")
        except Exception as e:
            print(f"  錯誤: {e}")
        print()
else:
    print("未找到包含'正德'的股票")
    
    # 列出所有股票供參考
    print("\n所有股票列表:")
    cursor.execute("SELECT code, name FROM stock_list ORDER BY code")
    all_stocks = cursor.fetchall()
    for stock in all_stocks[:20]:
        print(f"  {stock[0]} {stock[1]}")
    if len(all_stocks) > 20:
        print(f"  ... 還有 {len(all_stocks) - 20} 支")

conn.close()
