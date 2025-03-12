import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
	plugins: [react(), tailwindcss()],
	base: "/parlourbench/", // Add this line - replace with your repo name
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "./src"),
			"@data": path.resolve(__dirname, "../data"),
		},
	},
});
