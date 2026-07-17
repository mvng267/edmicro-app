"use client";

import { Card, CardContent, CardHeader, CardTitle, Chip, ChipLabel } from "@heroui/react";
import { useEffect, useState } from "react";

import { apiMe, type Me } from "@/lib/api";

export default function DashboardPage() {
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      window.location.href = "/login";
      return;
    }
    apiMe(token)
      .then(setMe)
      .catch(() => {
        window.location.href = "/login";
      });
  }, []);

  return (
    <main className="min-h-screen grid place-items-center bg-neutral-100 dark:bg-neutral-950 p-4">
      <Card className="w-full max-w-[480px]">
        <CardHeader>
          <CardTitle>Dashboard (M0 placeholder)</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {me ? (
            <>
              <p data-testid="greeting">Đăng nhập thành công 🎉</p>
              <div className="flex gap-2 items-center">
                <span className="text-sm text-neutral-500">Vai trò:</span>
                <Chip>
                  <ChipLabel data-testid="role">{me.role}</ChipLabel>
                </Chip>
              </div>
            </>
          ) : (
            <p>Đang tải…</p>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
