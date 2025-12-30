"""共用工具函數"""
import os
from datetime import datetime
from typing import Dict, Any

def load_env_config() -> Dict[str, str]:
    """載入環境變數配置"""
    from dotenv import load_dotenv
    load_dotenv()
    
    return {
        'finmind_token': os.getenv('Finmind_token', ''),
        'bedrock_api_key': os.getenv('BEDROCK_API_KEY', ''),
        'mcp_port': os.getenv('MCP_PORT', '8000'),
        'web_port': os.getenv('WEB_PORT', '5000')
    }

def format_date(date_str: str) -> str:
    """格式化日期字串"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        return date_str

def validate_stock_code(stock_code: str) -> bool:
    """驗證股票代碼格式"""
    return stock_code.isdigit() and len(stock_code) == 4