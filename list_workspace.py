#!/usr/bin/env python3
"""
List all available databases and their contents in Notion workspace.
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

def list_workspace_contents():
    """List all databases and their contents in the Notion workspace."""
    
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
        
        print("🔌 Connecting to Notion MCP server...")
        
        # Initialize the connection
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "workspace-explorer",
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
        
        # Search for all databases
        print("\n🔍 Searching for all databases in your workspace...")
        
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
                    },
                    "page_size": 100
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
                                print(f"\n📊 Found {len(databases)} database(s) in your workspace:")
                                print("=" * 60)
                                
                                for i, db in enumerate(databases, 1):
                                    db_id = db.get("id")
                                    db_title = "Untitled Database"
                                    
                                    # Extract database title
                                    if "title" in db and isinstance(db["title"], list):
                                        title_parts = [t.get("plain_text", "") for t in db["title"]]
                                        if title_parts:
                                            db_title = "".join(title_parts)
                                    
                                    print(f"\n{i}. 📋 Database: '{db_title}'")
                                    print(f"   🆔 ID: {db_id}")
                                    
                                    # Get database properties/schema
                                    if "properties" in db:
                                        print(f"   📝 Properties:")
                                        for prop_name, prop_info in db["properties"].items():
                                            prop_type = prop_info.get("type", "unknown")
                                            print(f"      • {prop_name}: {prop_type}")
                                    
                                    # Query this database for sample entries
                                    print(f"   📤 Querying for entries...")
                                    
                                    query_message = {
                                        "jsonrpc": "2.0",
                                        "id": 100 + i,
                                        "method": "tools/call",
                                        "params": {
                                            "name": "API-post-database-query",
                                            "arguments": {
                                                "database_id": db_id,
                                                "page_size": 5
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
                                                        entries = query_data["results"]
                                                        total_count = len(entries)
                                                        has_more = query_data.get("has_more", False)
                                                        
                                                        if has_more:
                                                            print(f"   🎫 Contains {total_count}+ entries (showing first {total_count}):")
                                                        else:
                                                            print(f"   🎫 Contains {total_count} entries:")
                                                        
                                                        # Show sample entries
                                                        for j, entry in enumerate(entries[:3], 1):
                                                            title = "Untitled"
                                                            status = ""
                                                            
                                                            if "properties" in entry:
                                                                # Look for title/name property
                                                                for prop_name, prop_value in entry["properties"].items():
                                                                    if prop_value.get("type") == "title" and prop_value.get("title"):
                                                                        title = "".join([t.get("plain_text", "") for t in prop_value["title"]])
                                                                    elif prop_value.get("type") == "select" and prop_value.get("select"):
                                                                        status = f" [{prop_value['select'].get('name', '')}]"
                                                                    elif prop_value.get("type") == "status" and prop_value.get("status"):
                                                                        status = f" [{prop_value['status'].get('name', '')}]"
                                                            
                                                            print(f"      {j}. {title}{status}")
                                                        
                                                        if total_count > 3:
                                                            remaining = total_count - 3
                                                            print(f"      ... and {remaining} more entries")
                                                        
                                                        # Highlight if this might contain tickets
                                                        keywords = ["refined", "ticket", "issue", "task", "bug", "feature", "story"]
                                                        if any(keyword in db_title.lower() for keyword in keywords):
                                                            print(f"   🎯 This might be your ticket database!")
                                                        
                                                except json.JSONDecodeError:
                                                    print(f"   ❌ Could not parse query response")
                                    else:
                                        print(f"   ❌ Failed to query database")
                                    
                                    print("-" * 40)
                            else:
                                print("\n📭 No databases found in your workspace")
                                
                    except json.JSONDecodeError:
                        print(f"Could not parse search response")
        else:
            print("❌ Search failed")
            if response and "error" in response:
                print(f"Error: {response['error']}")
        
        # Also search for pages to see what else is available
        print("\n\n🔍 Searching for pages in your workspace...")
        
        page_search_message = {
            "jsonrpc": "2.0",
            "id": 200,
            "method": "tools/call",
            "params": {
                "name": "API-post-search",
                "arguments": {
                    "filter": {
                        "property": "object",
                        "value": "page"
                    },
                    "page_size": 10
                }
            }
        }
        
        send_mcp_message(process, page_search_message)
        response = read_mcp_response(process)
        
        if response and "result" in response:
            search_content = response["result"].get("content", [])
            
            for content in search_content:
                if content.get("type") == "text":
                    try:
                        search_data = json.loads(content["text"])
                        if "results" in search_data:
                            pages = search_data["results"]
                            
                            if pages:
                                print(f"\n📄 Found {len(pages)} page(s) (showing first 10):")
                                
                                for i, page in enumerate(pages[:10], 1):
                                    page_title = "Untitled Page"
                                    
                                    # Extract page title
                                    if "properties" in page:
                                        for prop_name, prop_value in page["properties"].items():
                                            if prop_value.get("type") == "title" and prop_value.get("title"):
                                                page_title = "".join([t.get("plain_text", "") for t in prop_value["title"]])
                                                break
                                    
                                    print(f"   {i}. 📝 {page_title}")
                            else:
                                print("\n📭 No pages found")
                                
                    except json.JSONDecodeError:
                        print(f"Could not parse page search response")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'process' in locals():
            process.terminate()
            process.wait()

if __name__ == "__main__":
    list_workspace_contents()
