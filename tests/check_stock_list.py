import sqlite3
import os

os.chdir('..')

conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

# 檢查 stock_list 資料表
print("檢查 stock_list 資料表:")
print("=" * 60)

try:
    cursor.execute("SELECT * FROM stock_list ORDER BY code")
    stocks = cursor.fetchall()
    print(f"stock_list 中有 {len(stocks)} 筆資料\n")
    
    for stock in stocks[:10]:
        print(f"代碼: {stock[0]}, 名稱: {stock[1] if len(stock) > 1 else 'N/A'}")
    
    if len(stocks) > 10:
        print(f"... 還有 {len(stocks) - 10} 筆")
    
    # 檢查鴻海是否在列表中
    cursor.execute("SELECT * FROM stock_list WHERE code = '2317'")
    honhai = cursor.fetchone()
    print(f"\n鴻海(2317)在 stock_list 中: {'是' if honhai else '否'}")
    if honhai:
        print(f"  資料: {honhai}")
        
except Exception as e:
    print(f"stock_list 資料表不存在或有錯誤: {e}")

conn.close()
