import type { NextConfig } from "next";

// Backend FastAPI (nội bộ). Khi chạy sau tunnel/domain thật, browser gọi same-origin
// "/api/..." rồi Next proxy sang backend → không dính CORS lẫn mixed-content (https→http).
const API_ORIGIN = process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8010";

const nextConfig: NextConfig = {
	async rewrites() {
		return [{ source: "/api/:path*", destination: `${API_ORIGIN}/api/:path*` }];
	},
};

export default nextConfig;
