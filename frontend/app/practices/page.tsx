"use client";

import {
	Button,
	Card,
	CardContent,
	Chip,
	ChipLabel,
	Input,
} from "@heroui/react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
	type Branch,
	type Klass,
	type Practice,
	type QuestionRow,
	createAssignment,
	createPractice,
	listBranches,
	listClasses,
	listPractices,
	listQuestions,
} from "@/lib/api";

export default function PracticesPage() {
	const [questions, setQuestions] = useState<QuestionRow[]>([]);
	const [practices, setPractices] = useState<Practice[]>([]);
	const [classes, setClasses] = useState<Klass[]>([]);
	const [name, setName] = useState("");
	const [picked, setPicked] = useState<Set<string>>(new Set());
	const [assignClass, setAssignClass] = useState("");
	const [err, setErr] = useState("");
	const [msg, setMsg] = useState("");

	async function refresh() {
		setQuestions(await listQuestions({ status: "published" }));
		setPractices(await listPractices());
		setClasses(await listClasses());
	}
	// biome-ignore lint/correctness/useExhaustiveDependencies: chỉ load 1 lần
	useEffect(() => {
		refresh().catch((e) => setErr(String(e)));
	}, []);

	function toggle(id: string) {
		const next = new Set(picked);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		setPicked(next);
	}

	async function save() {
		setErr("");
		try {
			await createPractice(name, "reading", [...picked]);
			setName("");
			setPicked(new Set());
			await refresh();
			setMsg("Đã tạo bài luyện tập");
		} catch (e) {
			setErr(String(e));
		}
	}

	async function assign(practiceId: string) {
		setErr("");
		const classId = assignClass || classes[classes.length - 1]?.id;
		if (!classId) {
			setErr("Chưa có lớp để giao");
			return;
		}
		const due = new Date(Date.now() + 7 * 864e5).toISOString();
		try {
			const r = await createAssignment(practiceId, classId, due);
			setMsg(`Đã giao cho ${r.assignee_count} học sinh`);
		} catch (e) {
			setErr(String(e));
		}
	}

	return (
		<AppShell title="Bài luyện tập">
			<Card className="mb-4">
				<CardContent className="flex flex-col gap-3">
					<Input
						aria-label="Tên bài"
						placeholder="Tên bài luyện tập"
						data-testid="practice-name"
						value={name}
						onChange={(e) => setName(e.target.value)}
					/>
					<p className="text-sm text-neutral-500">Chọn câu hỏi đã xuất bản:</p>
					<ul data-testid="pick-list" className="flex flex-col gap-1">
						{questions.map((q) => (
							<li key={q.id} className="flex gap-2 items-center text-sm">
								<input
									type="checkbox"
									checked={picked.has(q.id)}
									onChange={() => toggle(q.id)}
									data-testid={`pick-${q.id}`}
								/>
								<Chip>
									<ChipLabel>{q.type}</ChipLabel>
								</Chip>
								<span className="text-neutral-500">{q.skill}</span>
							</li>
						))}
					</ul>
					<Button onPress={save} data-testid="save-practice">
						Tạo bài ({picked.size} câu)
					</Button>
					{msg && <p className="text-success-600 text-sm">{msg}</p>}
				</CardContent>
			</Card>

			{err && <p className="text-danger text-sm mb-2">{err}</p>}

			<div className="flex gap-2 mb-3 items-center">
				<span className="text-sm text-neutral-500">Giao cho lớp:</span>
				<select
					data-testid="assign-class"
					className="h-9 rounded-lg border px-2 bg-transparent text-sm"
					value={assignClass}
					onChange={(e) => setAssignClass(e.target.value)}
				>
					<option value="">Lớp mới nhất</option>
					{classes.map((c) => (
						<option key={c.id} value={c.id}>
							{c.name}
						</option>
					))}
				</select>
			</div>

			<ul data-testid="practice-list" className="flex flex-col gap-2">
				{practices.map((p) => (
					<li
						key={p.id}
						className="p-3 rounded-lg bg-white dark:bg-neutral-900 flex gap-3 items-center"
					>
						<span className="font-medium">{p.name}</span>
						<span className="text-neutral-500 text-sm">{p.n_q} câu</span>
						<Button onPress={() => assign(p.id)} data-testid={`assign-${p.id}`}>
							Giao cho lớp
						</Button>
					</li>
				))}
			</ul>
		</AppShell>
	);
}
