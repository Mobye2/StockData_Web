# 台積電股票K棒圖查詢系統

## 功能
- SQLite 資料庫儲存股票資料
- Web 介面顯示 K 棒圖
- 互動式圖表（可縮放、拖曳）
- 顯示成交量
- 回測系統（單檔/多檔）
- AI 分析功能（AWS Bedrock）

## 安裝套件
```bash
pip install flask pandas python-dotenv
```

## 環境設定

在專案根目錄創建 `.env` 檔案：

```
# FinMind API Token（用於股票資料擷取）
Finmind_token="你的_FinMind_Token"

# AWS Bedrock API Key（用於 AI 分析功能）
BEDROCK_API_KEY="你的_Bedrock_API_Key"
```

### 取得 FinMind Token
1. 前往 [FinMind 官網](https://finmindtrade.com/) 註冊帳號
2. 登入後在個人頁面取得 API Token

### 取得 Bedrock API Key
1. 登入 AWS Console
2. 前往 Bedrock 服務
3. 在 API Keys 頁面創建新的 API Key

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
- `backtest.py` - 回測引擎
- `templates/index.html` - K棒圖頁面
- `templates/single_backtest.html` - 單檔回測頁面
- `templates/multi_backtest.html` - 多檔回測頁面
- `.env` - 環境變數設定（需自行創建）
- `AI_SETUP.md` - AI 功能詳細設定說明
