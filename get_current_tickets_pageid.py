#!/usr/bin/env python3
"""
Find and print the page (row) ID for the entry titled 'Current Tickets' in the given database.
"""

import json
import subprocess
import os

DATABASE_ID = "c7698cc3-bd7e-4e1a-afde-2ed85ab3d9a7"

def send_mcp_message(process, message):
    json_message = json.dumps(message)
    process.stdin.write(json_message + '\n')
    process.stdin.flush()

def read_mcp_response(process):
    try:
        response = process.stdout.readline()
        if response:
            return json.loads(response.strip())
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None
    return None

def main():
    env = os.environ.copy()
    notion_token = os.environ.get("NOTION_TOKEN")
    if not notion_token:
        raise Exception("NOTION_TOKEN environment variable not set")
    env["OPENAPI_MCP_HEADERS"] = f'{{"Authorization":"Bearer {notion_token}","Notion-Version":"2022-06-28"}}'
    try:
        process = subprocess.Popen(
            ["docker", "run", "--rm", "-i", "-e", "OPENAPI_MCP_HEADERS", "mcp/notion"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        print(f"Querying database {DATABASE_ID} for all pages...")
        # Initialize
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "pageid-finder", "version": "1.0.0"}
            }
        }
        send_mcp_message(process, init_message)
        response = read_mcp_response(process)
        if not response or "result" not in response:
            print("❌ Failed to initialize MCP connection")
            return
        print("✅ Connected to Notion MCP server")
        # Query the database for all rows
        query_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "API-post-database-query",
                "arguments": {
                    "database_id": DATABASE_ID,
                    "page_size": 100
                }
            }
        }
        send_mcp_message(process, query_message)
        response = read_mcp_response(process)
        found = False
        if response and "result" in response:
            query_content = response["result"].get("content", [])
            for content in query_content:
                if content.get("type") == "text":
                    try:
                        query_data = json.loads(content["text"])
                        if "results" in query_data:
                            for page in query_data["results"]:
                                page_id = page.get("id")
                                title = "Untitled"
                                if "properties" in page:
                                    for prop_name, prop_value in page["properties"].items():
                                        if prop_value.get("type") == "title" and prop_value.get("title"):
                                            title = "".join([t.get("plain_text", "") for t in prop_value["title"]])
                                            break
                                print(f"Page: '{title}' | ID: {page_id}")
                                if title.strip().lower() == "current tickets":
                                    print(f"\n✅ Page ID for 'Current Tickets': {page_id}")
                                    found = True
                    except Exception as e:
                        print(f"Error parsing page: {e}")
        if not found:
            print("❌ Could not find a page titled 'Current Tickets' in the database.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'process' in locals():
            process.terminate()
            process.wait()

if __name__ == "__main__":
    main()
