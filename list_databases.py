#!/usr/bin/env python3
"""
List all Notion databases to find where tickets might be stored.
"""

import json
import subprocess

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

def list_all_databases():
    """List all available databases in Notion."""
    
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
                    "name": "database-lister",
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
        
        # Search for all databases (without filter)
        print("\n🔍 Searching for all databases...")
        
        search_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "API-post-search",
                "arguments": {
                    "filter": {
                        "property": "object",
                        "value": "database"
                    }
                }
            }
        }
        
        send_mcp_message(process, search_message)
        response = read_mcp_response(process)
        
        if response and "result" in response:
            search_content = response["result"].get("content", [])
            
            for content in search_content:
                if content.get("type") == "text":
                    try:
                        search_data = json.loads(content["text"])
                        if "results" in search_data:
                            databases = search_data["results"]
                            
                            if databases:
                                print(f"\n📊 Found {len(databases)} database(s):")
                                
                                for i, db in enumerate(databases, 1):
                                    db_id = db.get("id")
                                    db_title = "Untitled Database"
                                    
                                    # Extract database title
                                    if "title" in db and isinstance(db["title"], list):
                                        title_parts = [t.get("plain_text", "") for t in db["title"]]
                                        if title_parts:
                                            db_title = "".join(title_parts)
                                    
                                    print(f"  {i}. 📋 '{db_title}' (ID: {db_id[:8]}...)")
                                    
                                    # Check if this might be a ticket database
                                    keywords = ["refined", "ticket", "issue", "task", "bug", "feature"]
                                    if any(keyword in db_title.lower() for keyword in keywords):
                                        print(f"     🎯 This might contain tickets! Checking...")
                                        
                                        # Query this database for entry count
                                        query_message = {
                                            "jsonrpc": "2.0",
                                            "id": 3 + i,
                                            "method": "tools/call",
                                            "params": {
                                                "name": "API-post-database-query",
                                                "arguments": {
                                                    "database_id": db_id,
                                                    "page_size": 100
                                                }
                                            }
                                        }
                                        
                                        send_mcp_message(process, query_message)
                                        query_response = read_mcp_response(process)
                                        
                                        if query_response and "result" in query_response:
                                            query_content = query_response["result"].get("content", [])
                                            for qc in query_content:
                                                if qc.get("type") == "text":
                                                    try:
                                                        query_data = json.loads(qc["text"])
                                                        if "results" in query_data:
                                                            count = len(query_data["results"])
                                                            has_more = query_data.get("has_more", False)
                                                            total_text = f"{count}+" if has_more else str(count)
                                                            
                                                            print(f"     🎫 Contains {total_text} entries")
                                                            
                                                            if "refined" in db_title.lower():
                                                                print(f"\n✅ FOUND REFINED DATABASE!")
                                                                print(f"   📋 Database: '{db_title}'")
                                                                print(f"   🎫 Ticket Count: {total_text}")
                                                                return
                                                    except json.JSONDecodeError:
                                                        print(f"     ❌ Could not parse query response")
                            else:
                                print("No databases found")
                                
                    except json.JSONDecodeError:
                        print(f"Could not parse search response: {content['text'][:100]}...")
        else:
            print("❌ Search failed")
            if response and "error" in response:
                print(f"Error: {response['error']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'process' in locals():
            process.terminate()
            process.wait()

if __name__ == "__main__":
    list_all_databases()
