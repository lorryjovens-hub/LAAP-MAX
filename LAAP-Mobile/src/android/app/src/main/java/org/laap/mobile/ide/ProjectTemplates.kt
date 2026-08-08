package org.laap.mobile.ide

/**
 * Registry of built-in project templates. Keep the list small and
 * self-contained — each template ships its initial files as a literal
 * map so project creation needs zero network access.
 *
 * The sandbox resolves `/var/laap/projects/<id>/` to a host path, so
 * the template's relative `files` paths are written verbatim under that
 * directory; no path translation is needed here.
 *
 * Run-config commands assume the sandbox already has the toolchain
 * installed (Node, Python3, etc.) — the IDE does not bootstrap the
 * toolchain itself. The user (or an agent `shell_execute apk add …`)
 * does that once per rootfs.
 */
object ProjectTemplates {

    const val STATIC_HTML = "static-html"
    const val VITE_REACT = "vite-react"
    const val NODE_EXPRESS = "node-express"
    const val PYTHON_FLASK = "python-flask"
    const val PYTHON_SCRIPT = "python-script"

    val ALL: List<ProjectTemplate> = listOf(
        ProjectTemplate(
            id = STATIC_HTML,
            displayName = "Static HTML",
            description = "Single-page HTML + CSS + JS, no build step.",
            languageId = "html",
            files = mapOf(
                "index.html" to """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>My Static Page</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <main>
    <h1>Hello from LAAP</h1>
    <p>Edit <code>index.html</code> and tap Run to preview.</p>
    <button id="btn">Click me</button>
  </main>
  <script src="app.js"></script>
</body>
</html>
""",
                "styles.css" to """body {
  font-family: system-ui, sans-serif;
  margin: 0;
  padding: 2rem;
  background: #f5f5f7;
  color: #1d1d1f;
}
main { max-width: 720px; margin: 0 auto; }
h1 { color: #0071e3; }
button {
  padding: 0.5rem 1rem;
  border: 0;
  border-radius: 8px;
  background: #0071e3;
  color: white;
  font-size: 1rem;
}
""",
                "app.js" to """document.getElementById('btn').addEventListener('click', () => {
  alert('Hello from JS');
});
""",
            ),
            // Static HTML has no dev server: preview is served directly
            // via the existing `laap://` resource URL path.
            defaultRun = null,
        ),
        ProjectTemplate(
            id = VITE_REACT,
            displayName = "Vite + React",
            description = "Vite dev server on port 5173 with a tiny React counter.",
            languageId = "javascript",
            files = mapOf(
                "package.json" to """{
  "name": "vite-react-app",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host --port 5173"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.4.0"
  }
}
""",
                "vite.config.js" to """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: { host: true, port: 5173, strictPort: true },
});
""",
                "index.html" to """<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Vite + React</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""",
                "src/main.jsx" to """import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';

createRoot(document.getElementById('root')).render(<App />);
""",
                "src/App.jsx" to """import React, { useState } from 'react';

export default function App() {
  const [n, setN] = useState(0);
  return (
    <div style={{ fontFamily: 'system-ui', padding: '2rem' }}>
      <h1>Vite + React on LAAP</h1>
      <button onClick={() => setN(n + 1)}>count: {n}</button>
    </div>
  );
}
""",
            ),
            defaultRun = ProjectTemplate.RunConfig(
                name = "dev",
                command = "npm install && npm run dev",
                runType = "DEV_SERVER",
                port = 5173,
            ),
        ),
        ProjectTemplate(
            id = NODE_EXPRESS,
            displayName = "Node + Express",
            description = "Express server on port 3000 returning JSON.",
            languageId = "javascript",
            files = mapOf(
                "package.json" to """{
  "name": "node-express-app",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.19.2"
  }
}
""",
                "server.js" to """import express from 'express';

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.json({ ok: true, message: 'Hello from LAAP' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log('Server listening on http://localhost:' + PORT);
});
""",
            ),
            defaultRun = ProjectTemplate.RunConfig(
                name = "start",
                command = "npm install && npm start",
                runType = "DEV_SERVER",
                port = 3000,
            ),
        ),
        ProjectTemplate(
            id = PYTHON_FLASK,
            displayName = "Python + Flask",
            description = "Flask app on port 5000.",
            languageId = "python",
            files = mapOf(
                "app.py" to """from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify(ok=True, message='Hello from LAAP')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
""",
                "requirements.txt" to """flask>=3.0
""",
            ),
            defaultRun = ProjectTemplate.RunConfig(
                name = "run",
                command = "pip install -r requirements.txt && python app.py",
                runType = "DEV_SERVER",
                port = 5000,
            ),
        ),
        ProjectTemplate(
            id = PYTHON_SCRIPT,
            displayName = "Python Script",
            description = "Standalone Python script, runs to completion.",
            languageId = "python",
            files = mapOf(
                "main.py" to """#!/usr/bin/env python3
import sys

def main():
    print('Hello from LAAP', flush=True)
    for i in range(3):
        print(f'count {i}', flush=True)
    return 0

if __name__ == '__main__':
    sys.exit(main())
""",
            ),
            defaultRun = ProjectTemplate.RunConfig(
                name = "run",
                command = "python main.py",
                runType = "ONESHOT",
            ),
        ),
    )

    fun byId(id: String): ProjectTemplate? = ALL.firstOrNull { it.id == id }
}
