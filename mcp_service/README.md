# MCP 服務

Stock Analysis MCP Server - 提供股票數據查詢功能

## 功能

- **get_stock_list**: 獲取股票列表

## 啟動方式

```bash
python mcp_server.py
```

## 配置

資料庫路徑會自動檢測：
- 優先使用 `../stock.db`（從根目錄）
- 其次使用 `stock.db`（當前目錄）

## 依賴套件

見 `requirements_mcp.txt`