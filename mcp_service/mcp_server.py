#!/usr/bin/env python3
"""
Stock Analysis MCP Server - 超簡化版本
"""

import asyncio
import json
import sqlite3
import os
import sys
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ServerCapabilities

# 初始化MCP Server
server = Server("stock-analysis")

def get_db():
    """獲取資料庫連接"""
    db_path = '../stock.db' if not os.path.exists('stock.db') else 'stock.db'
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="get_stock_list",
            description="獲取股票列表",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """處理工具調用"""
    
    if name == "get_stock_list":
        conn = get_db()
        if not conn:
            return [TextContent(type="text", text="無法連接資料庫")]
        
        try:
            cursor = conn.execute('SELECT code, name FROM stock_list ORDER BY code LIMIT 5')
            rows = cursor.fetchall()
            stocks = [{"code": row['code'], "name": row['name']} for row in rows]
            return [TextContent(type="text", text=json.dumps(stocks, ensure_ascii=False, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"錯誤: {str(e)}")]
        finally:
            conn.close()
    
    return [TextContent(type="text", text=f"未知工具: {name}")]

async def main():
    """主函數"""
    print("啟動 MCP Server...", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        print("MCP Server 已啟動", file=sys.stderr)
        await server.run(
            read_stream, 
            write_stream,
            InitializationOptions(
                server_name="stock-analysis",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    tools={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())