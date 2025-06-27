#!/usr/bin/env python3
"""
Query the Notion MCP server to list all available actions/tools.
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

def list_mcp_capabilities():
    """List all capabilities and tools available in the Notion MCP server."""
    
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
                    "name": "capability-explorer",
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
        
        # Display server capabilities from initialization
        if "result" in response:
            server_info = response["result"]
            print(f"\n🤖 Server Information:")
            print(f"   📝 Protocol Version: {server_info.get('protocolVersion', 'Unknown')}")
            
            if "serverInfo" in server_info:
                server_details = server_info["serverInfo"]
                print(f"   🏷️  Name: {server_details.get('name', 'Unknown')}")
                print(f"   📊 Version: {server_details.get('version', 'Unknown')}")
            
            if "capabilities" in server_info:
                capabilities = server_info["capabilities"]
                print(f"\n🛠️  Server Capabilities:")
                for cap_name, cap_value in capabilities.items():
                    print(f"   • {cap_name}: {cap_value}")
        
        # List all available tools
        print("\n🔍 Querying available tools...")
        
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
            
            print(f"\n📋 Available Tools ({len(tools)} total):")
            print("=" * 80)
            
            # Group tools by category
            categories = {
                "Pages": [],
                "Databases": [],
                "Blocks": [],
                "Users": [],
                "Search": [],
                "Comments": [],
                "Other": []
            }
            
            for tool in tools:
                name = tool.get("name", "Unknown")
                description = tool.get("description", "No description available")
                
                # Categorize tools
                if "page" in name.lower():
                    categories["Pages"].append((name, description))
                elif "database" in name.lower():
                    categories["Databases"].append((name, description))
                elif "block" in name.lower():
                    categories["Blocks"].append((name, description))
                elif "user" in name.lower():
                    categories["Users"].append((name, description))
                elif "search" in name.lower():
                    categories["Search"].append((name, description))
                elif "comment" in name.lower():
                    categories["Comments"].append((name, description))
                else:
                    categories["Other"].append((name, description))
            
            # Display categorized tools
            for category, tools_list in categories.items():
                if tools_list:
                    print(f"\n📂 {category} ({len(tools_list)} tools):")
                    for i, (name, desc) in enumerate(tools_list, 1):
                        print(f"   {i:2d}. 🔧 {name}")
                        
                        # Format description with proper wrapping
                        if desc:
                            words = desc.split()
                            lines = []
                            current_line = []
                            current_length = 0
                            
                            for word in words:
                                if current_length + len(word) + 1 <= 60:  # 60 chars per line
                                    current_line.append(word)
                                    current_length += len(word) + 1
                                else:
                                    if current_line:
                                        lines.append(" ".join(current_line))
                                    current_line = [word]
                                    current_length = len(word)
                            
                            if current_line:
                                lines.append(" ".join(current_line))
                            
                            for line in lines:
                                print(f"       📄 {line}")
                        print()
        
        # List available resources
        print("\n🔍 Querying available resources...")
        
        resources_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
            "params": {}
        }
        
        send_mcp_message(process, resources_message)
        response = read_mcp_response(process)
        
        if response and "result" in response:
            resources = response["result"].get("resources", [])
            
            if resources:
                print(f"\n📚 Available Resources ({len(resources)} total):")
                for i, resource in enumerate(resources, 1):
                    name = resource.get("name", "Unknown")
                    description = resource.get("description", "No description")
                    uri = resource.get("uri", "No URI")
                    print(f"   {i}. 📦 {name}")
                    print(f"      📄 {description}")
                    print(f"      🔗 {uri}")
                    print()
            else:
                print("\n📚 No resources available")
        elif response and "error" in response:
            print(f"\nℹ️  Resources not supported: {response['error'].get('message', 'Unknown error')}")
        
        # List available prompts
        print("\n🔍 Querying available prompts...")
        
        prompts_message = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "prompts/list",
            "params": {}
        }
        
        send_mcp_message(process, prompts_message)
        response = read_mcp_response(process)
        
        if response and "result" in response:
            prompts = response["result"].get("prompts", [])
            
            if prompts:
                print(f"\n💬 Available Prompts ({len(prompts)} total):")
                for i, prompt in enumerate(prompts, 1):
                    name = prompt.get("name", "Unknown")
                    description = prompt.get("description", "No description")
                    print(f"   {i}. 💭 {name}")
                    print(f"      📄 {description}")
                    print()
            else:
                print("\n💬 No prompts available")
        elif response and "error" in response:
            print(f"\nℹ️  Prompts not supported: {response['error'].get('message', 'Unknown error')}")
        
        print("\n" + "=" * 80)
        print("🎯 Summary: This MCP server provides comprehensive Notion API access")
        print("   You can create, read, update, and delete pages, databases, and blocks")
        print("   Search functionality allows you to find content across your workspace")
        print("   User management and commenting features are also available")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'process' in locals():
            process.terminate()
            process.wait()

if __name__ == "__main__":
    list_mcp_capabilities()
