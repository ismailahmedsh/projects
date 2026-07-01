import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
// On GitHub Pages the site is served from /investment-portofolio/, so the
// production build needs that base. Dev server stays at the root.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/investment-portofolio/" : "/",
  plugins: [react()],
  server: {
    host: true, // listen on 0.0.0.0 so Codespaces can forward the port
    allowedHosts: true, // allow the *.app.github.dev proxy host
  },
}));
