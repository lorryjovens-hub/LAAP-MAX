import path from "path"
import fs from "fs"
import https from "https"
import type { IncomingMessage, ServerResponse } from "http"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

const LARGE_DOWNLOADS: Record<string, string> = {
  '/downloads/LAAP-Android.apk': 'd:\\\\LAAP\\\\LAAP-Mobile\\\\src\\\\android\\\\app\\\\build\\\\outputs\\\\apk\\\\release\\\\LAAP.apk',
  '/downloads/Aris-Pi-windows-x64.zip': path.join(process.env.TEMP || process.env.TMP || '.', 'Aris-Pi-windows-x64.zip'),
};

const SENSENOVA_API_KEY = process.env.SENSENOVA_API_KEY || 'sk-meeUtCHrW7Lne5MhQcTFZDvyMgk3mhTo';
const SENSENOVA_TARGET = 'https://token.sensenova.cn';

function serveLargeDownloads() {
  return {
    name: 'serve-large-downloads',
    configureServer(server: { middlewares: { use: (path: string, handler: (req: { url?: string; path?: string }, res: ServerResponse, next: () => void) => void) => void } }) {
      server.middlewares.use('/downloads', (req, res, next) => {
        const pathname = req.url?.split('?')[0] || '';
        const fullPath = '/downloads' + pathname;
        const sourcePath = LARGE_DOWNLOADS[fullPath];
        if (!sourcePath || !fs.existsSync(sourcePath)) {
          return next();
        }
        const stat = fs.statSync(sourcePath);
        const ext = path.extname(sourcePath);
        const contentType = ext === '.apk' ? 'application/vnd.android.package-archive' : 'application/zip';
        res.setHeader('Content-Type', contentType);
        res.setHeader('Content-Length', stat.size);
        res.setHeader('Content-Disposition', `attachment; filename="${path.basename(sourcePath)}"`);
        fs.createReadStream(sourcePath).pipe(res);
      });
    },
  };
}

function proxySenseNova() {
  return {
    name: 'proxy-sensenova',
    configureServer(server: { middlewares: { use: (path: string, handler: (req: IncomingMessage, res: ServerResponse, next: () => void) => void) => void } }) {
      server.middlewares.use('/api/sensenova', (req, res) => {
        const url = req.url || '';
        const targetPath = url.replace(/^\/api\/sensenova/, '/v1');
        const targetUrl = new URL(targetPath + (url.includes('?') ? '' : ''), SENSENOVA_TARGET);
        if (url.includes('?')) {
          targetUrl.search = url.split('?')[1];
        }

        const options: https.RequestOptions = {
          hostname: targetUrl.hostname,
          port: targetUrl.port || 443,
          path: targetUrl.pathname + targetUrl.search,
          method: req.method,
          headers: {
            ...req.headers,
            host: targetUrl.hostname,
            authorization: `Bearer ${SENSENOVA_API_KEY}`,
          },
        };

        const proxyReq = https.request(options, (proxyRes) => {
          res.writeHead(proxyRes.statusCode || 200, proxyRes.headers);
          proxyRes.pipe(res, { end: true });
        });

        proxyReq.on('error', (err) => {
          console.error('[SenseNova proxy] error:', err.message);
          res.statusCode = 502;
          res.end(JSON.stringify({ error: 'SenseNova proxy error', message: err.message }));
        });

        req.pipe(proxyReq, { end: true });
      });
    },
  };
}

// https://vite.dev/config/
export default defineConfig({
  base: process.env.VITE_BASE_URL || '/',
  plugins: [react(), serveLargeDownloads(), proxySenseNova()],
  assetsInclude: ['**/*.mp4', '**/*.webm', '**/*.ogg'],
  build: {
    assetsDir: 'assets',
    copyPublicDir: true,
    // 避免大公共资源在构建时因并发写入被锁定
    reportCompressedSize: false,
  },
  server: {
    port: 5173,
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
