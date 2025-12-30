"""
AI Tool Use 輔助函數
"""
import json
import sqlite3
import os

def get_db():
    """獲取資料庫連接"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'stock.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def execute_tool(tool_name, tool_input):
    """執行工具並返回結果"""
    print(f"DEBUG: 執行工具 {tool_name}，輸入參數: {tool_input}")
    
    if tool_name == "get_stock_data":
        stock_code = tool_input['stock_code']
        start_date = tool_input['start_date']
        end_date = tool_input['end_date']
        
        conn = get_db()
        try:
            cursor = conn.execute(
                f'SELECT * FROM stock_{stock_code} WHERE 日期 BETWEEN ? AND ? ORDER BY 日期',
                (start_date, end_date)
            )
            rows = cursor.fetchall()
            
            if not rows:
                result = "查無資料"
            else:
                # 表格格式輸出，節省token
                table = "日期\t開盤\t最高\t最低\t收盤\t成交量\n"
                for row in rows:
                    table += f"{row['日期']}\t{row['開盤價']:.2f}\t{row['最高價']:.2f}\t{row['最低價']:.2f}\t{row['收盤價']:.2f}\t{row['成交量']:,}\n"
                result = table
            
            print(f"DEBUG: 工具返回結果長度: {len(result)} 字元")
            return result
            
        except Exception as e:
            error_result = f"錯誤: {str(e)}"
            print(f"DEBUG: 工具執行錯誤: {error_result}")
            return error_result
        finally:
            conn.close()
    
    error_result = "未知的工具"
    print(f"DEBUG: 未知工具錯誤: {error_result}")
    return error_result

# 定義可用的工具
AVAILABLE_TOOLS = [
    {
        "name": "get_stock_data",
        "description": "查詢股票K棒資料，返回表格格式節省token",
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
