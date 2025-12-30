# 台積電股票K棒圖查詢系統 - 微服務架構

## 系統架構

```
StockData_Web/
├── main_app/                 # 主要 Web 應用程式
│   ├── web_app.py           # Flask 應用程式
│   ├── backtest.py          # 回測引擎
│   ├── templates/           # HTML 模板
│   ├── static/              # 靜態資源
│   └── requirements.txt     # Python 套件
├── mcp_service/             # MCP 獨立服務
│   ├── mcp_server.py        # MCP 伺服器
│   ├── config.json          # 服務配置
│   └── requirements_mcp.txt # MCP 套件
├── shared/                  # 共用模組
│   ├── database.py          # 資料庫管理
│   └── utils.py             # 工具函數
├── docker-compose.yml       # 容器編排
└── start_services.bat       # 服務啟動腳本
```

## 功能
- **Web 服務** (Port 5000): K棒圖顯示、回測系統
- **MCP 服務**: AI 分析、模型上下文協議
- **共用模組**: 資料庫連接、工具函數

## 快速啟動

### 方式一：腳本啟動（推薦）
```bash
start_services.bat
```

### 方式二：Docker 啟動
```bash
docker-compose up --build
```

### 方式三：手動啟動
```bash
# 啟動 MCP 服務
cd mcp_service
python mcp_server.py

# 啟動 Web 服務
cd main_app  
python web_app.py
```

## 服務端點
- Web 介面: http://localhost:5000
- MCP 服務: stdio 模式（背景運行）

## 環境設定
在根目錄創建 `.env` 檔案：
```
Finmind_token="你的_FinMind_Token"
BEDROCK_API_KEY="你的_Bedrock_API_Key"
```

## 資料獲取腳本
- `fetch_all_stocks.py` - 獲取所有股票資料
- `fetch_chip_data.py` - 獲取籌碼資料
- `fetch_daily_all.py` - 每日更新
- `fetch_hot_stock.py` - 熱門股票
- `fetch_sectors.py` - 產業分類