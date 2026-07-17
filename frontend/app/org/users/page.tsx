"use client";

import {
	Alert,
	AlertDescription,
	Button,
	Card,
	CardContent,
	Input,
} from "@heroui/react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
	type Credential,
	createUser,
	listUsers,
	type UserRow,
} from "@/lib/api";

export default function UsersPage() {
	const [users, setUsers] = useState<UserRow[]>([]);
	const [fullName, setFullName] = useState("");
	const [role, setRole] = useState("student");
	const [cred, setCred] = useState<Credential | null>(null);
	const [err, setErr] = useState("");

	async function refresh() {
		setUsers(await listUsers());
	}
	useEffect(() => {
		refresh().catch((e) => setErr(String(e)));
	}, []);

	async function add() {
		setErr("");
		try {
			const c = await createUser({ full_name: fullName, role });
			setCred(c);
			setFullName("");
			await refresh();
		} catch (e) {
			setErr(String(e));
		}
	}

	return (
		<AppShell title="Tài khoản">
			<Card className="mb-4">
				<CardContent className="flex flex-col gap-2">
					<div className="flex gap-2 items-end">
						<Input
							aria-label="Họ tên"
							placeholder="Họ tên"
							data-testid="user-name"
							value={fullName}
							onChange={(e) => setFullName(e.target.value)}
						/>
						<select
							data-testid="role-select"
							className="h-10 rounded-lg border px-2 bg-transparent"
							value={role}
							onChange={(e) => setRole(e.target.value)}
						>
							<option value="student">Học sinh</option>
							<option value="teacher">Giáo viên</option>
							<option value="assistant">Trợ giảng</option>
							<option value="parent">Phụ huynh</option>
						</select>
						<Button onPress={add} data-testid="add-user">
							Tạo tài khoản
						</Button>
					</div>
					{cred && (
						<Alert status="success" data-testid="cred-box">
							<AlertDescription>
								Tài khoản: <b data-testid="cred-username">{cred.username}</b> —
								Mật khẩu: <b data-testid="cred-password">{cred.password}</b>{" "}
								(chỉ hiện một lần)
							</AlertDescription>
						</Alert>
					)}
				</CardContent>
			</Card>
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			<ul data-testid="user-list" className="flex flex-col gap-2">
				{users.map((u) => (
					<li
						key={u.id}
						className="p-3 rounded-lg bg-white dark:bg-neutral-900 flex gap-2"
					>
						<span className="font-medium">{u.full_name}</span>
						<span className="text-neutral-500 text-sm">
							{u.username} · {u.role}
						</span>
					</li>
				))}
			</ul>
		</AppShell>
	);
}
