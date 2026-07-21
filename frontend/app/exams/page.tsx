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
	type BandRow,
	createAssignment,
	createExam,
	type ExamRow,
	type Klass,
	listClasses,
	listExams,
	listQuestions,
	type QuestionRow,
} from "@/lib/api";

// Bảng quy đổi band mặc định (gợi ý kiểu IELTS theo % đúng) — GV chỉnh khi cần.
const DEFAULT_SCALE: BandRow[] = [
	{ min: 0, band: "5.0" },
	{ min: 50, band: "6.0" },
	{ min: 65, band: "6.5" },
	{ min: 80, band: "7.0" },
	{ min: 90, band: "8.0+" },
];

export default function ExamsPage() {
	const [questions, setQuestions] = useState<QuestionRow[]>([]);
	const [exams, setExams] = useState<ExamRow[]>([]);
	const [classes, setClasses] = useState<Klass[]>([]);
	const [name, setName] = useState("");
	const [duration, setDuration] = useState("30");
	const [picked, setPicked] = useState<Set<string>>(new Set());
	const [assignClass, setAssignClass] = useState("");
	const [err, setErr] = useState("");
	const [msg, setMsg] = useState("");

	async function refresh() {
		setQuestions(await listQuestions({ status: "published" }));
		setExams(await listExams());
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
		const mins = Number(duration);
		if (Number.isNaN(mins) || mins <= 0) {
			setErr("Thời lượng phải là số phút > 0");
			return;
		}
		try {
			await createExam({
				name,
				question_ids: [...picked],
				duration_minutes: mins,
				band_scale: DEFAULT_SCALE,
			});
			setName("");
			setPicked(new Set());
			await refresh();
			setMsg("Đã tạo đề thi");
		} catch (e) {
			setErr(String(e));
		}
	}

	async function assign(examId: string) {
		setErr("");
		const classId = assignClass || classes[classes.length - 1]?.id;
		if (!classId) {
			setErr("Chưa có lớp để giao");
			return;
		}
		const due = new Date(Date.now() + 7 * 864e5).toISOString();
		try {
			const r = await createAssignment(examId, classId, due);
			setMsg(`Đã giao cho ${r.assignee_count} học sinh`);
		} catch (e) {
			setErr(String(e));
		}
	}

	return (
		<AppShell title="Đề thi">
			<Card className="mb-4">
				<CardContent className="flex flex-col gap-3">
					<div className="flex gap-2">
						<Input
							aria-label="Tên đề thi"
							placeholder="Tên đề thi"
							data-testid="exam-name"
							value={name}
							onChange={(e) => setName(e.target.value)}
						/>
						<Input
							aria-label="Thời lượng (phút)"
							placeholder="Phút"
							className="w-28"
							data-testid="exam-duration"
							value={duration}
							onChange={(e) => setDuration(e.target.value)}
						/>
					</div>
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
								<span className="font-medium">{q.prompt}</span>
								<span className="text-neutral-500">{q.skill}</span>
							</li>
						))}
					</ul>
					<Button onPress={save} data-testid="save-exam">
						Tạo đề ({picked.size} câu · {duration}′)
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

			<ul data-testid="exam-list" className="flex flex-col gap-2">
				{exams.map((e) => (
					<li
						key={e.id}
						className="p-3 rounded-lg bg-white dark:bg-neutral-900 flex gap-3 items-center"
					>
						<span className="font-medium">{e.name}</span>
						<span className="text-neutral-500 text-sm">
							{e.n_q} câu · {e.duration_minutes}′
						</span>
						<Button onPress={() => assign(e.id)} data-testid={`assign-${e.id}`}>
							Giao cho lớp
						</Button>
					</li>
				))}
			</ul>
		</AppShell>
	);
}
