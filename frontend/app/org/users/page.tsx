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
	type Klass,
	listClasses,
	listUsers,
	type UserRow,
} from "@/lib/api";

export default function UsersPage() {
	const [users, setUsers] = useState<UserRow[]>([]);
	const [classes, setClasses] = useState<Klass[]>([]);
	const [fullName, setFullName] = useState("");
	const [role, setRole] = useState("student");
	const [classId, setClassId] = useState("");
	const [cred, setCred] = useState<Credential | null>(null);
	const [err, setErr] = useState("");
	// bộ lọc danh sách
	const [q, setQ] = useState("");
	const [roleFilter, setRoleFilter] = useState("");

	async function refresh() {
		setUsers(await listUsers(q || undefined, roleFilter || undefined));
		setClasses(await listClasses());
	}
	// biome-ignore lint/correctness/useExhaustiveDependencies: refresh phụ thuộc bộ lọc
	useEffect(() => {
		refresh().catch((e) => setErr(String(e)));
	}, [q, roleFilter]);

	async function add() {
		setErr("");
		try {
			const c = await createUser({
				full_name: fullName,
				role,
				class_id: role === "student" && classId ? classId : undefined,
			});
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
						{role === "student" && (
							<select
								data-testid="user-class"
								className="h-10 rounded-lg border px-2 bg-transparent"
								value={classId}
								onChange={(e) => setClassId(e.target.value)}
							>
								<option value="">— Chưa xếp lớp —</option>
								{classes.map((c) => (
									<option key={c.id} value={c.id}>
										{c.name}
									</option>
								))}
							</select>
						)}
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
			<div className="flex gap-2 mb-3 flex-wrap items-center">
				<input
					placeholder="Tìm theo tên / tài khoản…"
					aria-label="Tìm kiếm"
					data-testid="user-search"
					value={q}
					onChange={(e) => setQ(e.target.value)}
					className="h-9 rounded-lg border px-3 text-sm bg-white dark:bg-neutral-900 min-w-56"
				/>
				<select
					data-testid="user-role-filter"
					className="h-9 rounded-lg border px-2 bg-white dark:bg-neutral-900 text-sm"
					value={roleFilter}
					onChange={(e) => setRoleFilter(e.target.value)}
				>
					<option value="">Mọi vai trò</option>
					<option value="student">Học sinh</option>
					<option value="teacher">Giáo viên</option>
					<option value="assistant">Trợ giảng</option>
					<option value="manager">Quản lý</option>
					<option value="parent">Phụ huynh</option>
				</select>
				<span className="text-xs text-neutral-500">
					{users.length} tài khoản
				</span>
			</div>
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
