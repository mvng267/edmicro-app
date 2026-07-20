import { defineConfig } from "@playwright/test";

export default defineConfig({
	testDir: "./e2e",
	timeout: 30_000,
	// Chạy tuần tự: mọi test dùng chung 1 backend + DB dev (tránh nhiễu chéo).
	workers: 1,
	fullyParallel: false,
	use: {
		baseURL: "http://bright.localhost:3005",
	},
});
