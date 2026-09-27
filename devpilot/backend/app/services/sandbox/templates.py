"""
Starter files written into a freshly created workspace, keyed by
`ProjectTemplate`. Kept deliberately small — the point of DevPilot is that
the agent grows the project from here, not that we ship a large boilerplate.

Content strings are passed through `str.format(name=..., slug=...)`, so any
literal `{` / `}` that is NOT a `{name}`/`{slug}` placeholder must be escaped
as `{{` / `}}`.
"""

PYTHON_TEMPLATE = {
    "README.md": "# {name}\n\nA plain Python project scaffolded by DevPilot.\n\n"
    "Run it with:\n\n```bash\npython app/main.py\n```\n\n"
    "Run tests with:\n\n```bash\npytest\n```\n",
    "app/main.py": "def greet(name: str) -> str:\n"
    '    """Return a friendly greeting for `name`."""\n'
    '    return f"Hello, {{name}}!"\n\n\n'
    'if __name__ == "__main__":\n'
    '    print(greet("world"))\n',
    "tests/test_main.py": "from app.main import greet\n\n\n"
    "def test_greet():\n"
    '    assert greet("DevPilot") == "Hello, DevPilot!"\n',
}

FASTAPI_TEMPLATE = {
    "README.md": "# {name}\n\nA small FastAPI app scaffolded by DevPilot.\n\n"
    "Run it with:\n\n```bash\nuvicorn app.main:app --reload\n```\n\n"
    "Run tests with:\n\n```bash\npytest\n```\n",
    "app/main.py": "from fastapi import FastAPI\n\n"
    'app = FastAPI(title="{name}")\n\n\n'
    '@app.get("/health")\n'
    "def health() -> dict:\n"
    '    return {{"status": "ok"}}\n\n\n'
    '@app.get("/users/{{user_id}}")\n'
    "def get_user(user_id: int) -> dict:\n"
    '    return {{"id": user_id, "name": f"user-{{user_id}}"}}\n',
    "tests/test_api.py": "from fastapi.testclient import TestClient\n\n"
    "from app.main import app\n\n"
    "client = TestClient(app)\n\n\n"
    "def test_health():\n"
    '    response = client.get("/health")\n'
    "    assert response.status_code == 200\n"
    '    assert response.json() == {{"status": "ok"}}\n',
    "requirements.txt": "fastapi\nuvicorn[standard]\npytest\nhttpx\n",
}

REACT_TEMPLATE = {
    "README.md": "# {name}\n\nA small React + TypeScript scaffold created by DevPilot.\n\n"
    "Install dependencies and start the dev server with:\n\n```bash\nnpm install\nnpm run dev\n```\n",
    "src/App.tsx": "export default function App() {{\n"
    "  return (\n"
    "    <main>\n"
    "      <h1>{name}</h1>\n"
    "      <p>Scaffolded by DevPilot. Ask the agent to build something.</p>\n"
    "    </main>\n"
    "  );\n"
    "}}\n",
    "src/main.tsx": 'import React from "react";\n'
    'import ReactDOM from "react-dom/client";\n\n'
    'import App from "./App";\n\n'
    'ReactDOM.createRoot(document.getElementById("root")!).render(\n'
    "  <React.StrictMode>\n"
    "    <App />\n"
    "  </React.StrictMode>\n"
    ");\n",
    "package.json": '{{\n  "name": "{slug}",\n  "private": true,\n  "version": "0.1.0",\n'
    '  "scripts": {{ "dev": "vite" }}\n}}\n',
}

NODE_TEMPLATE = {
    "README.md": "# {name}\n\nA plain Node.js project scaffolded by DevPilot.\n\n"
    "Run it with:\n\n```bash\nnode index.js\n```\n\n"
    "Run tests with:\n\n```bash\nnode --test\n```\n",
    "index.js": "function greet(name) {{\n"
    "  return `Hello, ${{name}}!`;\n"
    "}}\n\n"
    "module.exports = {{ greet }};\n\n"
    'if (require.main === module) {{\n  console.log(greet("world"));\n}}\n',
    "index.test.js": 'const test = require("node:test");\n'
    'const assert = require("node:assert");\n'
    'const {{ greet }} = require("./index");\n\n'
    'test("greet returns a friendly message", () => {{\n'
    '  assert.strictEqual(greet("DevPilot"), "Hello, DevPilot!");\n'
    "}});\n",
}

TEMPLATES: dict[str, dict[str, str]] = {
    "python": PYTHON_TEMPLATE,
    "fastapi": FASTAPI_TEMPLATE,
    "react": REACT_TEMPLATE,
    "node": NODE_TEMPLATE,
}


def render_template(template: str, project_name: str) -> dict[str, str]:
    """Return {relative_path: content} for `template`, with {name}/{slug} filled in."""
    slug = "-".join(project_name.strip().lower().split()) or "devpilot-project"
    files = TEMPLATES.get(template, PYTHON_TEMPLATE)
    return {path: content.format(name=project_name, slug=slug) for path, content in files.items()}
