import { fileURLToPath } from 'node:url'

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  nitro: {
    output: {
      publicDir: fileURLToPath(new URL('./dist', import.meta.url))
    }
  }
})
