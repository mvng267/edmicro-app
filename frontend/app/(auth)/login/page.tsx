"use client";

import {
  Alert,
  AlertDescription,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Label,
  TextField,
} from "@heroui/react";
import { useState } from "react";

import { apiLogin, tenantSlugFromHost } from "@/lib/api";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const slug = tenantSlugFromHost();
      const r = await apiLogin(slug, username, password);
      localStorage.setItem("access_token", r.access_token);
      localStorage.setItem("refresh_token", r.refresh_token);
      window.location.href = "/dashboard";
    } catch {
      setError("Sai tên đăng nhập hoặc mật khẩu");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen grid place-items-center bg-neutral-100 dark:bg-neutral-950 p-4">
      <Card className="w-full max-w-[420px]">
        <CardHeader>
          <CardTitle>Đăng nhập</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <TextField>
              <Label>Tên đăng nhập</Label>
              <Input
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </TextField>
            <TextField>
              <Label>Mật khẩu</Label>
              <Input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </TextField>
            {error && (
              <Alert status="danger">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Button type="submit" isDisabled={loading} className="w-full">
              {loading ? "Đang đăng nhập…" : "Đăng nhập"}
            </Button>
          </form>
          <p className="mt-4 text-xs text-neutral-500">
            Học sinh dùng tài khoản do trung tâm cấp. Quên mật khẩu? Liên hệ giáo viên hoặc trung
            tâm.
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
