import { NextRequest, NextResponse } from "next/server";

// Resolve tenant slug từ subdomain (bright.localhost:3000 -> "bright")
// và truyền xuống client qua header để lib/api gắn X-Tenant-Slug khi gọi backend.
export function middleware(req: NextRequest) {
  const host = req.headers.get("host") ?? "";
  const hostname = host.split(":")[0];
  const sub = hostname.split(".")[0];
  const isReserved = ["www", "localhost", "ops"].includes(sub) || sub.startsWith("127");
  const slug = sub && !isReserved ? sub : "";
  const res = NextResponse.next();
  res.headers.set("x-tenant-slug", slug);
  return res;
}

export const config = { matcher: ["/((?!_next|favicon.ico).*)"] };
