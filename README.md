# 台積電股票K棒圖查詢系統

## 功能
- SQLite 資料庫儲存股票資料
- Web 介面顯示 K 棒圖
- 互動式圖表（可縮放、拖曳）
- 顯示成交量

## 安裝套件
```bash
pip install flask pandas
```

## 使用步驟

### 1. 建立資料庫
```bash
python create_db.py
```

### 2. 啟動 Web 服務
```bash
python web_app.py
```

### 3. 開啟瀏覽器
訪問: http://localhost:5000

## 資料庫查詢範例

```python
import sqlite3

conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

# 查詢最近10筆資料
cursor.execute('SELECT * FROM tsmc_daily ORDER BY 日期 DESC LIMIT 10')
print(cursor.fetchall())

# 查詢特定日期範圍
cursor.execute("SELECT * FROM tsmc_daily WHERE 日期 BETWEEN '2024-08-01' AND '2024-08-31'")
print(cursor.fetchall())

# 計算平均收盤價
cursor.execute('SELECT AVG(收盤價) FROM tsmc_daily')
print(cursor.fetchone())

conn.close()
```

## 檔案說明
- `stock.db` - SQLite 資料庫
- `web_app.py` - Flask Web 應用程式
- `create_db.py` - 建立資料庫腳本
- `templates/index.html` - K棒圖頁面
