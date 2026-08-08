import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

const root = __dirname

export default defineConfig(({ mode }) => {
  if (mode === 'main') {
    return {
      plugins: [],
      build: {
        ssr: true,
        lib: {
          entry: path.resolve(root, 'electron/main.ts'),
          formats: ['cjs'],
          fileName: () => 'main.cjs',
        },
        outDir: path.resolve(root, 'dist-electron/main'),
        emptyOutDir: true,
        rollupOptions: {
          external: ['electron'],
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
    }
  }

  if (mode === 'preload') {
    return {
      plugins: [],
      build: {
        lib: {
          entry: path.resolve(root, 'electron/preload.ts'),
          formats: ['cjs'],
          fileName: () => 'preload.cjs',
        },
        outDir: path.resolve(root, 'dist-electron/preload'),
        emptyOutDir: true,
        rollupOptions: {
          external: ['electron'],
        },
      },
    }
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
  }
})
