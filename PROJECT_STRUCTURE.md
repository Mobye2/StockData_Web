# 專案結構說明

## 核心目錄

### main_app/ - 主要 Web 應用
- `web_app.py` - Flask 主程式
- `backtest.py` - 回測引擎
- `templates/` - HTML 模板
- `static/` - 靜態資源（JS, CSS）
- `requirements.txt` - Python 依賴

### mcp_service/ - MCP 服務
- `mcp_server.py` - MCP 伺服器（已優化，可正常運行）
- `config.json` - 服務配置
- `requirements_mcp.txt` - MCP 依賴
- `README.md` - MCP 服務說明

### shared/ - 共用模組
- `database.py` - 資料庫管理類
- `utils.py` - 工具函數

## 資料獲取腳本（根目錄）
- `fetch_all_stocks.py` - 獲取所有股票資料
- `fetch_chip_data.py` - 獲取籌碼資料
- `fetch_daily_all.py` - 每日更新
- `fetch_hot_stock.py` - 熱門股票
- `fetch_sectors.py` - 產業分類

## 配置文件
- `.env` - 環境變數（API Keys）
- `.env.example` - 環境變數範例
- `Pipfile` - Pipenv 配置
- `docker-compose.yml` - Docker 編排

## 啟動腳本
- `start_services.bat` - 一鍵啟動所有服務

## 資料文件
- `stock.db` - SQLite 資料庫
- `stock_list.csv` - 股票列表
- `strategies.json` - 回測策略

## 參考資料（可選）
- `reference/` - 參考文件和範例
- `tests/` - 測試文件
- `DB.Browser.for.SQLite*/` - 資料庫瀏覽工具

## 已清理的檔案
以下檔案已被刪除或整合：
- ❌ `mcp_server_simple.py`
- ❌ `mcp_minimal.py`
- ❌ `mcp_ultra_simple.py`
- ❌ `test_mcp.py`
- ❌ `api_server.py`
- ❌ `mcp_agent.py`
- ❌ `mcp_config.json`
- ❌ `start_pipenv.bat`
- ❌ `Pipfile.lock`

✅ 最終使用：`mcp_server.py`（已優化並可正常運行）