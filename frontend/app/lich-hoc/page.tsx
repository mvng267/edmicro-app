"use client";

import { Button, Card, CardContent, Input } from "@heroui/react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
	type AttendanceRow,
	type ClassSession,
	createSession,
	getAttendance,
	type Klass,
	listClasses,
	listSessions,
	markAttendance,
} from "@/lib/api";

const STATUSES = [
	{ v: "present", l: "Có mặt" },
	{ v: "late", l: "Muộn" },
	{ v: "excused", l: "Có phép" },
	{ v: "absent", l: "Vắng" },
];

export default function SchedulePage() {
	const [classes, setClasses] = useState<Klass[]>([]);
	const [classId, setClassId] = useState("");
	const [sessions, setSessions] = useState<ClassSession[]>([]);
	const [start, setStart] = useState("");
	const [end, setEnd] = useState("");
	const [topic, setTopic] = useState("");
	const [openId, setOpenId] = useState("");
	const [roster, setRoster] = useState<Record<string, string>>({});
	const [rosterRows, setRosterRows] = useState<AttendanceRow[]>([]);
	const [err, setErr] = useState("");
	const [msg, setMsg] = useState("");

	useEffect(() => {
		listClasses()
			.then((cs) => {
				setClasses(cs);
				if (cs.length) setClassId(cs[cs.length - 1].id);
			})
			.catch((e) => setErr(String(e)));
	}, []);

	useEffect(() => {
		if (!classId) return;
		listSessions(classId)
			.then(setSessions)
			.catch((e) => setErr(String(e)));
	}, [classId]);

	async function refreshSessions() {
		if (classId) setSessions(await listSessions(classId));
	}

	async function addSession() {
		setErr("");
		if (!start || !end) {
			setErr("Chọn giờ bắt đầu và kết thúc");
			return;
		}
		try {
			await createSession({
				class_id: classId,
				starts_at: new Date(start).toISOString(),
				ends_at: new Date(end).toISOString(),
				topic,
			});
			setTopic("");
			await refreshSessions();
			setMsg("Đã tạo buổi học");
		} catch (e) {
			setErr(String(e));
		}
	}

	async function openAttendance(sessionId: string) {
		setOpenId(sessionId);
		setMsg("");
		const rows = await getAttendance(sessionId);
		setRosterRows(rows);
		// mặc định "tất cả có mặt rồi chỉnh lệch"
		const init: Record<string, string> = {};
		for (const r of rows) init[r.student_id] = r.status ?? "present";
		setRoster(init);
	}

	async function saveAttendance() {
		setErr("");
		try {
			const records = rosterRows.map((r) => ({
				student_id: r.student_id,
				status: roster[r.student_id] ?? "present",
			}));
			const res = await markAttendance(openId, records);
			setMsg(`Đã điểm danh (${res.absent} vắng)`);
		} catch (e) {
			setErr(String(e));
		}
	}

	return (
		<AppShell title="Lịch học & điểm danh">
			<div className="flex gap-2 mb-4 items-center">
				<span className="text-sm text-neutral-500">Lớp:</span>
				<select
					value={classId}
					onChange={(e) => setClassId(e.target.value)}
					data-testid="class-select"
					className="border rounded-lg px-2 py-1 text-sm bg-white dark:bg-neutral-900"
				>
					{classes.map((c) => (
						<option key={c.id} value={c.id}>
							{c.name}
						</option>
					))}
				</select>
			</div>

			<Card className="mb-4">
				<CardContent className="flex flex-wrap gap-2 items-end">
					<label className="text-sm flex flex-col gap-1">
						Bắt đầu
						<input
							type="datetime-local"
							value={start}
							onChange={(e) => setStart(e.target.value)}
							data-testid="session-start"
							className="border rounded-lg px-2 py-1 bg-white dark:bg-neutral-900"
						/>
					</label>
					<label className="text-sm flex flex-col gap-1">
						Kết thúc
						<input
							type="datetime-local"
							value={end}
							onChange={(e) => setEnd(e.target.value)}
							data-testid="session-end"
							className="border rounded-lg px-2 py-1 bg-white dark:bg-neutral-900"
						/>
					</label>
					<Input
						aria-label="Chủ đề buổi học"
						placeholder="Chủ đề"
						className="min-w-40"
						value={topic}
						onChange={(e) => setTopic(e.target.value)}
						data-testid="session-topic"
					/>
					<Button onPress={addSession} data-testid="add-session">
						Tạo buổi
					</Button>
				</CardContent>
			</Card>

			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			{msg && <p className="text-success-600 text-sm mb-2">{msg}</p>}

			<ul data-testid="session-list" className="flex flex-col gap-2">
				{sessions.map((se) => (
					<li key={se.id}>
						<Card data-testid={`session-${se.id}`}>
							<CardContent className="flex flex-col gap-2">
								<div className="flex items-center gap-3">
									<span className="font-medium">
										{se.starts_at.slice(0, 16).replace("T", " ")}
									</span>
									<span className="text-sm text-neutral-500">{se.topic}</span>
									<Button
										variant="ghost"
										className="ml-auto"
										onPress={() => openAttendance(se.id)}
										data-testid={`take-${se.id}`}
									>
										Điểm danh
									</Button>
								</div>

								{openId === se.id && (
									<div className="flex flex-col gap-2 border-t border-neutral-200 dark:border-neutral-800 pt-2">
										{rosterRows.map((r) => (
											<div
												key={r.student_id}
												className="flex items-center gap-2 text-sm"
											>
												<span className="flex-1">{r.full_name}</span>
												<select
													value={roster[r.student_id] ?? "present"}
													onChange={(e) =>
														setRoster((m) => ({
															...m,
															[r.student_id]: e.target.value,
														}))
													}
													data-testid={`att-${r.student_id}`}
													className="border rounded-lg px-2 py-1 bg-white dark:bg-neutral-900"
												>
													{STATUSES.map((st) => (
														<option key={st.v} value={st.v}>
															{st.l}
														</option>
													))}
												</select>
											</div>
										))}
										<Button
											onPress={saveAttendance}
											data-testid="save-attendance"
										>
											Lưu điểm danh
										</Button>
									</div>
								)}
							</CardContent>
						</Card>
					</li>
				))}
			</ul>
		</AppShell>
	);
}
