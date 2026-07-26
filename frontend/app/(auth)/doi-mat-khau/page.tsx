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

import { changePassword } from "@/lib/api";

export default function ChangePasswordPage() {
	const [oldPw, setOldPw] = useState("");
	const [newPw, setNewPw] = useState("");
	const [confirm, setConfirm] = useState("");
	const [error, setError] = useState("");
	const [loading, setLoading] = useState(false);

	async function onSubmit(e: React.FormEvent) {
		e.preventDefault();
		setError("");
		if (newPw.length < 8) {
			setError("Mật khẩu mới phải từ 8 ký tự");
			return;
		}
		if (newPw !== confirm) {
			setError("Xác nhận mật khẩu không khớp");
			return;
		}
		setLoading(true);
		try {
			await changePassword(oldPw, newPw);
			window.location.href = "/dashboard";
		} catch {
			setError("Mật khẩu hiện tại không đúng");
		} finally {
			setLoading(false);
		}
	}

	return (
		<main className="min-h-screen grid place-items-center bg-neutral-100 dark:bg-neutral-950 p-4">
			<Card className="w-full max-w-[420px]">
				<CardHeader>
					<CardTitle>Đổi mật khẩu</CardTitle>
				</CardHeader>
				<CardContent>
					<p className="text-sm text-neutral-500 mb-4">
						Bạn đang dùng mật khẩu tạm do trung tâm cấp. Hãy đặt mật khẩu mới
						(tối thiểu 8 ký tự) để tiếp tục.
					</p>
					<form onSubmit={onSubmit} className="flex flex-col gap-4">
						<TextField>
							<Label>Mật khẩu hiện tại</Label>
							<Input
								type="password"
								autoComplete="current-password"
								value={oldPw}
								onChange={(e) => setOldPw(e.target.value)}
							/>
						</TextField>
						<TextField>
							<Label>Mật khẩu mới</Label>
							<Input
								type="password"
								autoComplete="new-password"
								value={newPw}
								onChange={(e) => setNewPw(e.target.value)}
							/>
						</TextField>
						<TextField>
							<Label>Nhập lại mật khẩu mới</Label>
							<Input
								type="password"
								autoComplete="new-password"
								value={confirm}
								onChange={(e) => setConfirm(e.target.value)}
							/>
						</TextField>
						{error && (
							<Alert status="danger">
								<AlertDescription>{error}</AlertDescription>
							</Alert>
						)}
						<Button type="submit" isDisabled={loading} className="w-full">
							{loading ? "Đang lưu…" : "Đổi mật khẩu và vào học"}
						</Button>
					</form>
				</CardContent>
			</Card>
		</main>
	);
}
