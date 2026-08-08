import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
var root = __dirname;
export default defineConfig(function (_a) {
    var mode = _a.mode;
    if (mode === 'main') {
        return {
            plugins: [],
            build: {
                ssr: true,
                lib: {
                    entry: path.resolve(root, 'electron/main.ts'),
                    formats: ['cjs'],
                    fileName: function () { return 'main.cjs'; },
                },
                outDir: path.resolve(root, 'dist-electron/main'),
                emptyOutDir: true,
                rollupOptions: {
                    external: ['electron', 'ws'],
                    output: {
                        inlineDynamicImports: true,
                    },
                },
            },
            resolve: {
                alias: {
                    '@': path.resolve(root, 'src'),
                },
            },
        };
    }
    if (mode === 'preload') {
        return {
            plugins: [],
            build: {
                lib: {
                    entry: path.resolve(root, 'electron/preload.ts'),
                    formats: ['cjs'],
                    fileName: function () { return 'preload.cjs'; },
                },
                outDir: path.resolve(root, 'dist-electron/preload'),
                emptyOutDir: true,
                rollupOptions: {
                    external: ['electron'],
                },
            },
        };
    }
    return {
        root: path.resolve(root, 'src'),
        publicDir: path.resolve(root, 'public'),
        plugins: [react()],
        resolve: {
            alias: {
                '@': path.resolve(root, 'src'),
            },
        },
        build: {
            outDir: path.resolve(root, 'dist'),
            emptyOutDir: true,
            rollupOptions: {
                input: {
                    index: path.resolve(root, 'src/index.html'),
                    overlay: path.resolve(root, 'src/overlay.html'),
                },
            },
        },
        server: {
            port: 5173,
        },
    };
});
