import sqlite3

conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

# 查詢所有資料表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print(f"資料庫共有 {len(tables)} 個表：\n")

for table in tables:
    table_name = table[0]
    
    if table_name == 'stock_list':
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"[LIST] {table_name}: {count} 支股票")
        
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        print("  前5筆:", cursor.fetchall())
    else:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute(f"SELECT MIN(日期), MAX(日期) FROM {table_name}")
            date_range = cursor.fetchone()
            print(f"[OK] {table_name}: {count} 筆 ({date_range[0]} ~ {date_range[1]})")
        else:
            print(f"[EMPTY] {table_name}: 無資料")

conn.close()
