import { defineConfig } from "@playwright/test";

export default defineConfig({
	testDir: "./e2e",
	// Timeout rộng: Next dev biên dịch route on-demand lần đầu có thể chậm (cold compile).
	timeout: 60_000,
	expect: { timeout: 10_000 },
	// Chạy tuần tự: mọi test dùng chung 1 backend + DB dev (tránh nhiễu chéo).
	workers: 1,
	fullyParallel: false,
	use: {
		baseURL: "http://bright.localhost:3005",
	},
});
