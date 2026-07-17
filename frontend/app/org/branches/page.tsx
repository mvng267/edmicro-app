"use client";

import { Button, Card, CardContent, Input } from "@heroui/react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { type Branch, createBranch, listBranches } from "@/lib/api";

export default function BranchesPage() {
	const [branches, setBranches] = useState<Branch[]>([]);
	const [name, setName] = useState("");
	const [err, setErr] = useState("");

	async function refresh() {
		try {
			setBranches(await listBranches());
		} catch (e) {
			setErr(String(e));
		}
	}
	useEffect(() => {
		refresh();
	}, []);

	async function add() {
		setErr("");
		try {
			await createBranch(name);
			setName("");
			await refresh();
		} catch (e) {
			setErr(String(e));
		}
	}

	return (
		<AppShell title="Chi nhánh">
			<Card className="mb-4">
				<CardContent className="flex flex-row gap-2 items-end">
					<Input
						aria-label="Tên chi nhánh"
						placeholder="Tên chi nhánh"
						data-testid="branch-name"
						value={name}
						onChange={(e) => setName(e.target.value)}
					/>
					<Button onPress={add} data-testid="add-branch">
						Thêm
					</Button>
				</CardContent>
			</Card>
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			<ul data-testid="branch-list" className="flex flex-col gap-2">
				{branches.map((b) => (
					<li
						key={b.id}
						className="p-3 rounded-lg bg-white dark:bg-neutral-900"
					>
						{b.name}
					</li>
				))}
			</ul>
		</AppShell>
	);
}
