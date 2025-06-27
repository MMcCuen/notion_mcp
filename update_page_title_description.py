#!/usr/bin/env python3
"""
Update the title and description of an existing Notion page by page ID.
"""

import json
import subprocess
import os
import argparse

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
    parser = argparse.ArgumentParser(description="Update a Notion page's title and description by page ID.")
    parser.add_argument('--id', required=True, help='The Notion page ID to update')
    parser.add_argument('--title', required=True, help='The new title for the page')
    parser.add_argument('--description', required=False, default='', help='The new description for the page')
    args = parser.parse_args()
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
        print(f"Updating page {args.id} with new title and description...")
        # Initialize
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "page-updater", "version": "1.0.0"}
            }
        }
        send_mcp_message(process, init_message)
        response = read_mcp_response(process)
        if not response or "result" not in response:
            print("❌ Failed to initialize MCP connection")
            return
        print("✅ Connected to Notion MCP server")
        # Update the page title
        patch_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "API-patch-page",
                "arguments": {
                    "page_id": args.id,
                    "properties": {
                        "title": [
                            {"type": "text", "text": {"content": args.title}}
                        ]
                    }
                }
            }
        }
        send_mcp_message(process, patch_message)
        response = read_mcp_response(process)
        if response and "result" in response:
            print(f"✅ Title updated to: {args.title}")
        else:
            print("❌ Failed to update title.")
        # Update the description (as a new paragraph block)
        if args.description:
            block_message = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "API-patch-block-children",
                    "arguments": {
                        "block_id": args.id,
                        "children": [
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {"type": "text", "text": {"content": args.description}}
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
            send_mcp_message(process, block_message)
            response = read_mcp_response(process)
            if response and "result" in response:
                print(f"✅ Description updated.")
            else:
                print("❌ Failed to update description.")
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
