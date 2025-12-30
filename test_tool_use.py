"""
測試 Bedrock Tool Use 功能
"""
import json
import os
from urllib.request import Request, urlopen
from dotenv import load_dotenv

load_dotenv()

# 定義工具
tools = [
    {
        "name": "get_stock_data",
        "description": "查詢股票K棒資料",
        "input_schema": {
            "type": "object",
            "properties": {
                "stock_code": {
                    "type": "string",
                    "description": "股票代碼，例如：2330"
                },
                "start_date": {
                    "type": "string",
                    "description": "開始日期，格式：YYYY-MM-DD"
                },
                "end_date": {
                    "type": "string",
                    "description": "結束日期，格式：YYYY-MM-DD"
                }
            },
            "required": ["stock_code", "start_date", "end_date"]
        }
    }
]

# 準備請求
payload = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1000,
    "tools": tools,
    "messages": [
        {
            "role": "user",
            "content": "請幫我查詢台積電(2330)在2024-01-01到2024-01-10的股價資料"
        }
    ]
}

api_key = os.getenv('BEDROCK_API_KEY')

req = Request(
    'https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-sonnet-4-20250514-v1:0/invoke',
    data=json.dumps(payload).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
)

print("發送請求...")
with urlopen(req, timeout=30) as response:
    result = json.loads(response.read().decode('utf-8'))
    print("\n回應:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 檢查是否有工具調用
    if result.get('stop_reason') == 'tool_use':
        print("\n✅ AI 要求調用工具！")
        for content in result['content']:
            if content['type'] == 'tool_use':
                print(f"工具名稱: {content['name']}")
                print(f"工具參數: {json.dumps(content['input'], ensure_ascii=False, indent=2)}")
    else:
        print(f"\n❌ stop_reason: {result.get('stop_reason')}")
