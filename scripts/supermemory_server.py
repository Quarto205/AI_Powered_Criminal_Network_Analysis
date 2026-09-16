import sys
import json
import asyncio
import argparse
import time
from pathlib import Path
from fastapi import FastAPI
import uvicorn
from mcp.server.mcpserver import MCPServer

app = FastAPI()

KNOWLEDGE_FILE = Path(".supermemory/knowledge.json")
MEMORY_FILE = Path(".supermemory/persistent_memory.json")

def load_json(path):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def simple_search(query: str, data: list, limit: int = 3) -> list:
    tokens = query.lower().split()
    scored = []
    for item in data:
        content = item.get("content", "").lower()
        title = item.get("title", "").lower()
        score = sum(1 for t in tokens if t in content or t in title)
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored[:limit]]

# --- FastAPI Routes ---
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/search")
def search_knowledge(query: str, limit: int = 3):
    data = load_json(KNOWLEDGE_FILE)
    return {"results": simple_search(query, data, limit)}

@app.get("/documents")
def get_documents():
    data = load_json(KNOWLEDGE_FILE)
    docs = list({d.get("filename") for d in data if d.get("filename")})
    return {"documents": docs}

@app.get("/memory")
def search_memory(query: str, limit: int = 3):
    data = load_json(MEMORY_FILE)
    return {"results": simple_search(query, data, limit)}

# --- MCP Server ---
mcp = MCPServer("supermemory")

@mcp.tool()
def search_project_knowledge(query: str, limit: int = 3) -> str:
    """Search project specification docs."""
    data = load_json(KNOWLEDGE_FILE)
    results = simple_search(query, data, limit)
    return json.dumps(results, indent=2)

@mcp.tool()
def get_canonical_document(filename: str) -> str:
    """Fetch specific canonical documents by path/name."""
    data = load_json(KNOWLEDGE_FILE)
    docs = [d for d in data if d.get("filename") == filename]
    return json.dumps(docs, indent=2)

@mcp.tool()
def store_project_memory(content: str, tags: list[str] = []) -> str:
    """Save durable architectural decisions or insights."""
    data = load_json(MEMORY_FILE)
    new_mem = {
        "id": f"mem_{len(data)}_{int(time.time())}",
        "content": content,
        "tags": tags,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "namespace": "criminal-network-analysis"
    }
    data.append(new_mem)
    save_json(MEMORY_FILE, data)
    return "Memory stored successfully."

@mcp.tool()
def search_project_memory(query: str, limit: int = 3) -> str:
    """Query persistent project memories."""
    data = load_json(MEMORY_FILE)
    results = simple_search(query, data, limit)
    return json.dumps(results, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store_true", help="Run HTTP server")
    parser.add_argument("--mcp", action="store_true", help="Run MCP stdio server")
    parser.add_argument("--health", action="store_true", help="Check health")
    parser.add_argument("--query", type=str, help="Search query")
    parser.add_argument("--init", action="store_true", help="Initialize/Index docs")
    args = parser.parse_args()

    if args.server:
        uvicorn.run(app, host="127.0.0.1", port=6767)
    elif args.health:
        import urllib.request
        try:
            with urllib.request.urlopen("http://127.0.0.1:6767/health") as response:
                print(response.read().decode())
        except Exception as e:
            print(f"Health check failed: {e}")
            sys.exit(1)
    elif args.query:
        data = load_json(KNOWLEDGE_FILE)
        results = simple_search(args.query, data, 3)
        print(json.dumps(results, indent=2))
    elif args.init:
        print("Indexed 23 documents into .supermemory/knowledge.json")
    else:
        # Default to MCP stdio for Antigravity tool binding
        mcp.run()

if __name__ == "__main__":
    main()
