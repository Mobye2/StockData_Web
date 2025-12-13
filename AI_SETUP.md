# AI 分析功能設定說明

## 1. 安裝必要套件

```bash
pip install python-dotenv
```

（如果已經安裝則可跳過）

## 2. 設定 API Key

在專案根目錄創建 `.env` 檔案：

```
BEDROCK_API_KEY=你的_API_Key
```

## 3. 測試 AI 連線

1. 啟動 Flask 應用程式：`python web_app.py`
2. 開啟瀏覽器訪問回測頁面：http://localhost:5000/backtest
3. 點擊「測試AI連線」按鈕
4. 如果顯示綠色勾勾和 AI 回應，表示設定成功

## 4. 使用 AI 分析

1. 執行回測後，在結果區域會看到「🤖 AI分析」按鈕
2. 點擊按鈕，AI 會分析回測結果並提供：
   - 策略表現分析
   - 優缺點評估
   - 改進建議
   - 風險提示

## 注意事項

- 確保已在 AWS Bedrock 中創建 API Key
- 確保已啟用 Claude 3 Sonnet 模型
- .env 檔案不應提交到版本控制系統
- 使用 Python 內建 urllib 發送 HTTP 請求，不需要安裝額外套件
