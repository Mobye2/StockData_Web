import sqlite3
import sys
import os

os.chdir('..')
sys.path.append('..')

# 直接測試 web_app.py 的邏輯
print("測試 web_app.py 讀取鴻海資料的邏輯")
print("=" * 80)

conn = sqlite3.connect('stock.db')
conn.row_factory = sqlite3.Row

# 測試讀取鴻海資料
stock_code = '2317'
table_name = f'stock_{stock_code}'

print(f"\n1. 測試讀取 {table_name}")
try:
    cursor = conn.execute(f'SELECT * FROM {table_name} ORDER BY 日期')
    rows = cursor.fetchall()
    data = [dict(row) for row in rows]
    
    print(f"   成功讀取 {len(data)} 筆資料")
    
    if len(data) > 0:
        print(f"\n   第一筆資料:")
        first = data[0]
        for key in first.keys():
            print(f"     {key}: {first[key]}")
        
        print(f"\n   最後一筆資料:")
        last = data[-1]
        for key in last.keys():
            print(f"     {key}: {last[key]}")
        
        # 計算 MA
        print(f"\n   計算移動平均線...")
        for i in range(len(data)):
            if i >= 4:
                ma5 = sum(data[j]['收盤價'] for j in range(i-4, i+1)) / 5
                data[i]['MA5'] = round(ma5, 2)
            if i >= 9:
                ma10 = sum(data[j]['收盤價'] for j in range(i-9, i+1)) / 10
                data[i]['MA10'] = round(ma10, 2)
            if i >= 19:
                ma20 = sum(data[j]['收盤價'] for j in range(i-19, i+1)) / 20
                data[i]['MA20'] = round(ma20, 2)
        
        print(f"   MA 計算完成")
        print(f"\n   最後一筆資料 (含MA):")
        last_with_ma = data[-1]
        print(f"     日期: {last_with_ma['日期']}")
        print(f"     收盤價: {last_with_ma['收盤價']}")
        print(f"     MA5: {last_with_ma.get('MA5', 'N/A')}")
        print(f"     MA10: {last_with_ma.get('MA10', 'N/A')}")
        print(f"     MA20: {last_with_ma.get('MA20', 'N/A')}")
        
except Exception as e:
    print(f"   錯誤: {e}")
    import traceback
    traceback.print_exc()

conn.close()

# 測試 stock_list
print(f"\n2. 測試 stock_list 中的鴻海")
conn = sqlite3.connect('stock.db')
conn.row_factory = sqlite3.Row

try:
    cursor = conn.execute('SELECT code, name FROM stock_list WHERE code = "2317"')
    row = cursor.fetchone()
    if row:
        print(f"   找到: {dict(row)}")
    else:
        print(f"   未找到鴻海")
except Exception as e:
    print(f"   錯誤: {e}")

conn.close()

print("\n" + "=" * 80)
