# mcp_server.py

from mcp.server.fastmcp import FastMCP
import os
import glob

# Nombre del proyecto para identificar en la IA
mcp = FastMCP("DjangoProject")

# Función para leer archivos solicitados por la IA
@mcp.resource("file://{path}")
def read_file(path: str) -> str:
    full = os.path.abspath(os.path.join(os.getcwd(), path))
    try:
        if os.path.isfile(full) and full.endswith((
            '.py', '.html', '.js', '.css', '.md', '.txt', '.json', '.yml', '.yaml'
        )):
            with open(full, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
    return "File not found or not supported."

# Herramienta para listar archivos por patrón (máximo 50)
@mcp.tool()
def list_project_files(pattern: str = "**/*.py") -> str:
    """Lista archivos del proyecto Django con un patrón específico."""
    files = glob.glob(pattern, recursive=True)
    return "\n".join(files[:50])

# Herramienta para ver estructura general del proyecto
@mcp.tool()
def get_project_structure() -> str:
    """Muestra la estructura de carpetas y archivos del proyecto."""
    structure = []
    for root, dirs, files in os.walk(".", topdown=True):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
        level = root.replace(".", "").count(os.sep)
        indent = "  " * level
        structure.append(f"{indent}{os.path.basename(root)}/")
        subindent = "  " * (level + 1)
        for file in files:
            if not file.startswith('.') and not file.endswith('.pyc'):
                structure.append(f"{subindent}{file}")
    return "\n".join(structure)

# Inicia el servidor MCP
if __name__ == "__main__":
    mcp.run(transport="stdio")
