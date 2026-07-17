"use client";

import { Button, Card, CardContent, Input } from "@heroui/react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
	type Branch,
	createClass,
	type Klass,
	listBranches,
	listClasses,
} from "@/lib/api";

export default function ClassesPage() {
	const [branches, setBranches] = useState<Branch[]>([]);
	const [classes, setClasses] = useState<Klass[]>([]);
	const [branchId, setBranchId] = useState("");
	const [name, setName] = useState("");
	const [err, setErr] = useState("");

	async function refresh() {
		setBranches(await listBranches());
		setClasses(await listClasses());
	}
	useEffect(() => {
		refresh().catch((e) => setErr(String(e)));
	}, []);

	async function add() {
		setErr("");
		try {
			await createClass(branchId || branches[0]?.id, name, "en");
			setName("");
			await refresh();
		} catch (e) {
			setErr(String(e));
		}
	}

	return (
		<AppShell title="Lớp học">
			<Card className="mb-4">
				<CardContent className="flex flex-col gap-2">
					<select
						data-testid="branch-select"
						className="h-10 rounded-lg border px-2 bg-transparent"
						value={branchId}
						onChange={(e) => setBranchId(e.target.value)}
					>
						<option value="">— Chọn chi nhánh —</option>
						{branches.map((b) => (
							<option key={b.id} value={b.id}>
								{b.name}
							</option>
						))}
					</select>
					<div className="flex gap-2 items-end">
						<Input
							aria-label="Tên lớp"
							placeholder="Tên lớp"
							data-testid="class-name"
							value={name}
							onChange={(e) => setName(e.target.value)}
						/>
						<Button onPress={add} data-testid="add-class">
							Thêm lớp
						</Button>
					</div>
				</CardContent>
			</Card>
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			<ul data-testid="class-list" className="flex flex-col gap-2">
				{classes.map((c) => (
					<li
						key={c.id}
						className="p-3 rounded-lg bg-white dark:bg-neutral-900"
					>
						{c.name}{" "}
						<span className="text-neutral-500 text-sm">({c.language})</span>
					</li>
				))}
			</ul>
		</AppShell>
	);
}
