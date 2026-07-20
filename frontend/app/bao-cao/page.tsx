"use client";

import { Card, CardContent } from "@heroui/react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
	type ClassReport,
	classReport,
	type Klass,
	listClasses,
} from "@/lib/api";

export default function ClassReportPage() {
	const [classes, setClasses] = useState<Klass[]>([]);
	const [classId, setClassId] = useState("");
	const [report, setReport] = useState<ClassReport | null>(null);
	const [err, setErr] = useState("");

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
		setErr("");
		classReport(classId)
			.then(setReport)
			.catch((e) => setErr(String(e)));
	}, [classId]);

	return (
		<AppShell title="Báo cáo lớp">
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

			{report && (
				<div className="flex flex-col gap-4">
					<div className="flex gap-3">
						<Card className="flex-1">
							<CardContent>
								<p className="text-sm text-neutral-500">Điểm TB lớp</p>
								<p
									className="text-2xl font-bold text-primary"
									data-testid="class-avg"
								>
									{report.summary.class_avg ?? "—"}
								</p>
							</CardContent>
						</Card>
						<Card className="flex-1">
							<CardContent>
								<p className="text-sm text-neutral-500">Tỉ lệ hoàn thành</p>
								<p className="text-2xl font-bold" data-testid="completion-rate">
									{report.summary.completion_rate === null
										? "—"
										: `${Math.round(report.summary.completion_rate * 100)}%`}
								</p>
							</CardContent>
						</Card>
						<Card className="flex-1">
							<CardContent>
								<p className="text-sm text-neutral-500">Sĩ số</p>
								<p className="text-2xl font-bold">
									{report.summary.student_count}
								</p>
							</CardContent>
						</Card>
					</div>

					<Card>
						<CardContent className="p-0 overflow-x-auto">
							<table className="w-full text-sm" data-testid="student-table">
								<thead>
									<tr className="text-left text-neutral-500 border-b border-neutral-200 dark:border-neutral-800">
										<th className="p-3">Học sinh</th>
										<th className="p-3">Đã nộp</th>
										<th className="p-3">Điểm TB</th>
									</tr>
								</thead>
								<tbody>
									{report.students.map((st) => (
										<tr
											key={st.student_id}
											className="border-b border-neutral-100 dark:border-neutral-800"
											data-testid={`row-${st.student_id}`}
										>
											<td className="p-3 font-medium">
												<Link
													href={`/bao-cao/hoc-sinh/${st.student_id}`}
													className="text-primary hover:underline"
												>
													{st.full_name}
												</Link>
											</td>
											<td className="p-3">
												{st.submitted}/{st.assigned}
											</td>
											<td className="p-3">{st.avg_score ?? "—"}</td>
										</tr>
									))}
								</tbody>
							</table>
						</CardContent>
					</Card>
				</div>
			)}
		</AppShell>
	);
}
