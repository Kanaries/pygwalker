import { defineConfig, ConfigEnv, UserConfig } from 'vite'
import path from 'path';
import react from '@vitejs/plugin-react'
import typescript from '@rollup/plugin-typescript'
import { peerDependencies } from './package.json'
import Replace from '@rollup/plugin-replace'
import CommonJs from '@rollup/plugin-commonjs'
import Terser from '@rollup/plugin-terser'

// @see https://styled-components.com/docs/faqs#marking-styledcomponents-as-external-in-your-package-dependencies
const modulesNotToBundle = Object.keys(peerDependencies);

// https://vitejs.dev/config/
export default defineConfig((config: ConfigEnv) => {
  console.log("defineConfig: ", config);
  return {
    server: {
      port: 2002,
    },
    plugins: [
      react(),
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
      ... (config.mode === 'production') ? [CommonJs(), Terser()]: []
    ],
    resolve: {
      //dedupe: modulesNotToBundle,
    },
    build: {
      lib: {
        entry: path.resolve(__dirname, './src/index.tsx'),
        name: 'PyGWalkerApp',
        fileName: (format) => `pygwalker-app.${format}.js`,
        formats: ['iife']
      },
      rollupOptions: {
        // external: modulesNotToBundle,
        // output: {
        //   globals: {
        //     'react': 'React',
        //     'react-dom': 'ReactDOM',
        //     'styled-components': 'styled',
        //   },
        // },
      },
      minify: 'terser', // 'esbuild',
      // sourcemap: true,
      sourcemap: false,
      outDir: '../pygwalker/templates/dist'
    }
  } as UserConfig;
})
