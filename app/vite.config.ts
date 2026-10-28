import { defineConfig, ConfigEnv, UserConfig } from 'vite'
import wasm from 'vite-plugin-wasm';
import path from 'path';
import react from '@vitejs/plugin-react'
import typescript from '@rollup/plugin-typescript'
import { peerDependencies } from './package.json'
import Replace from '@rollup/plugin-replace'

// @see https://styled-components.com/docs/faqs#marking-styledcomponents-as-external-in-your-package-dependencies
const modulesNotToBundle = Object.keys(peerDependencies);

// https://vitejs.dev/config/
export default defineConfig((config: ConfigEnv) => {
  const buildConfigMap = {
    "production": {
      lib: {
        entry: path.resolve(__dirname, './src/index.tsx'),
        name: 'PyGWalkerApp',
        fileName: (format) => `pygwalker-app.${format}.js`,
        formats: ['iife', "es"]
      },
      minify: 'esbuild',
      sourcemap: false,
      outDir: '../pygwalker/templates/dist'
    },
    "dsl_to_workflow": {
      lib: {
        entry: path.resolve(__dirname, "./src/lib/dslToWorkflow.ts"),
        name: "main",
        formats: ["umd"],
        fileName: (format) => `dsl-to-workflow.${format}.js`,
      },
      minify: "esbuild",
      sourcemap: false,
      outDir: '../pygwalker/templates/dist'
    },
    "vega_to_dsl": {
      lib: {
        entry: path.resolve(__dirname, "./src/lib/vegaToDsl.ts"),
        name: "main",
        formats: ["umd"],
        fileName: (format) => `vega-to-dsl.${format}.js`,
      },
      minify: "esbuild",
      sourcemap: false,
      outDir: '../pygwalker/templates/dist'
    }
  }

  return {
    base: "/pyg_dev_app/",
    // The browser bundle only probes Node's `process` global for optional environment
    // switches. Inline a minimal browser value so downstream bundlers (including the
    // JupyterLab prebuilt-extension builder) do not inject `process/browser` while reparsing
    // the generated ESM bundle.
    define: {
      process: JSON.stringify({ env: { NODE_ENV: config.mode } }),
    },
    server: {
      port: 8769,
    },
    optimizeDeps: {
      exclude: ['@kanaries/gw-dsl-parser'],
    },
    plugins: [
      react(),
      wasm(),
      // @ts-ignore
      {
        ...typescript({
          tsconfig: path.resolve(__dirname, './tsconfig.json'),
        }),
        apply: 'build'
      },
      Replace({
        'process.env.NODE_ENV': JSON.stringify(config.mode),
        'preventAssignment': true
      }),
    ],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    build: {
      ...buildConfigMap[config.mode],
      rollupOptions: {
        external: modulesNotToBundle,
        output: {
          manualChunks: undefined,
          inlineDynamicImports: true,
          globals: {
            'react': 'React',
            'react-dom': 'ReactDOM',
            'styled-components': 'styled',
          },
        },
      },
    }
  } as UserConfig;
})
