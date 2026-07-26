"use client";

import { Card, CardContent } from "@heroui/react";
import { Medal } from "lucide-react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
	type Klass,
	type LeaderRow,
	leaderboard,
	listClasses,
} from "@/lib/api";

export default function LeaderboardPage() {
	const [classes, setClasses] = useState<Klass[]>([]);
	const [classId, setClassId] = useState("");
	const [rows, setRows] = useState<LeaderRow[]>([]);
	const [err, setErr] = useState("");

	useEffect(() => {
		listClasses()
			.then((cs) => {
				const sorted = [...cs].sort((a, b) => a.name.localeCompare(b.name));
				setClasses(sorted);
				if (sorted.length) setClassId(sorted[0].id);
			})
			.catch((e) => setErr(String(e)));
	}, []);

	useEffect(() => {
		if (!classId) return;
		setErr("");
		leaderboard(classId)
			.then(setRows)
			.catch((e) => setErr(String(e)));
	}, [classId]);

	return (
		<AppShell title="Bảng xếp hạng">
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
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			<Card>
				<CardContent className="p-0 overflow-x-auto">
					<table className="w-full text-sm" data-testid="leaderboard">
						<thead>
							<tr className="text-left text-neutral-500 border-b border-neutral-200 dark:border-neutral-800">
								<th className="p-3 w-12">#</th>
								<th className="p-3">Học sinh</th>
								<th className="p-3">Điểm</th>
							</tr>
						</thead>
						<tbody>
							{rows.map((r) => (
								<tr
									key={r.student_id}
									className="border-b border-neutral-100 dark:border-neutral-800"
								>
									<td className="p-3 font-semibold">
										{r.rank <= 3 ? (
											<Medal
												size={18}
												className={
													r.rank === 1
														? "text-yellow-500"
														: r.rank === 2
															? "text-neutral-400"
															: "text-amber-700"
												}
												aria-label={`Hạng ${r.rank}`}
											/>
										) : (
											r.rank
										)}
									</td>
									<td className="p-3">{r.full_name}</td>
									<td className="p-3">{r.points}</td>
								</tr>
							))}
						</tbody>
					</table>
				</CardContent>
			</Card>
		</AppShell>
	);
}
