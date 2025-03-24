import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
	plugins: [react(), tailwindcss()],
	base: "/", // For custom domain, use root path
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "./src"),
			"@data": path.resolve(__dirname, "../data"),
		},
	},
	server: {
		historyApiFallback: true, // Support for BrowserRouter
	},
	build: {
		outDir: "dist",
	},
});
