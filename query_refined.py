#!/usr/bin/env python3
"""
Query Notion MCP server to find ticket information in Refined database.
"""

import json
import subprocess
import sys
import os

def send_mcp_message(process, message):
    """Send a JSON-RPC message to the MCP server."""
    json_message = json.dumps(message)
    process.stdin.write(json_message + '\n')
    process.stdin.flush()

def read_mcp_response(process):
    """Read a response from the MCP server."""
    try:
        response = process.stdout.readline()
        if response:
            return json.loads(response.strip())
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None
    return None

def query_refined_tickets():
    """Query Notion for tickets in Refined database."""
    
    # Environment setup for Docker
    env = os.environ.copy()
    notion_token = os.environ.get("NOTION_TOKEN")
    if not notion_token:
        raise Exception("NOTION_TOKEN environment variable not set")
    env["OPENAPI_MCP_HEADERS"] = f'{{"Authorization":"Bearer {notion_token}","Notion-Version":"2022-06-28"}}'

    try:
        # Start the MCP server
        process = subprocess.Popen(
            ["docker", "run", "--rm", "-i", "-e", "OPENAPI_MCP_HEADERS", "mcp/notion"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        print("Connecting to Notion MCP server...")
        
        # Initialize the connection
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "refined-ticket-counter",
                    "version": "1.0.0"
                }
            }
        }
        
        send_mcp_message(process, init_message)
        response = read_mcp_response(process)
        
        if not response or "result" not in response:
            print("❌ Failed to initialize MCP connection")
            return
        
        print("✅ Connected to Notion MCP server")
        
        # List available tools
        tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        send_mcp_message(process, tools_message)
        response = read_mcp_response(process)
        
        if response and "result" in response:
            tools = response["result"].get("tools", [])
            print(f"Found {len(tools)} available tools:")
            
            # Look for database query tools
            query_tools = [tool for tool in tools if "database" in tool.get("name", "").lower() or "query" in tool.get("name", "").lower()]
            
            if query_tools:
                print("Database query tools found:")
                for tool in query_tools:
                    print(f"  - {tool.get('name')}: {tool.get('description', 'No description')}")
                
                # Try to use a database query tool to find Refined tickets
                # This is a generic approach - the actual tool name may vary
                if query_tools:
                    tool_name = query_tools[0]["name"]
                    
                    # Attempt to query for databases containing "refined" or tickets
                    query_message = {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": {
                                "query": "refined tickets"
                            }
                        }
                    }
                    
                    send_mcp_message(process, query_message)
                    response = read_mcp_response(process)
                    
                    if response and "result" in response:
                        print("Query results:")
                        print(json.dumps(response["result"], indent=2))
                    else:
                        print("No results from database query")
            else:
                print("No database query tools found. Available tools:")
                for tool in tools:
                    print(f"  - {tool.get('name')}: {tool.get('description', 'No description')}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'process' in locals():
            process.terminate()
            process.wait()

if __name__ == "__main__":
    query_refined_tickets()
