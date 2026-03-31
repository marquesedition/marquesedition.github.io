import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://www.marquesedition.com",
  output: "static",
  trailingSlash: "always",
  i18n: {
    locales: ["es", "en"],
    defaultLocale: "es",
    routing: {
      prefixDefaultLocale: false,
    },
  },
});
