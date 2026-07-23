"use client";

import { Card, CardContent, Chip, ChipLabel } from "@heroui/react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { StudentReportView } from "@/components/StudentReportView";
import {
	type Child,
	childPoints,
	childReport,
	myChildren,
	type PointsSummary,
	type StudentReport,
} from "@/lib/api";

export default function ParentPage() {
	const [children, setChildren] = useState<Child[]>([]);
	const [sel, setSel] = useState("");
	const [report, setReport] = useState<StudentReport | null>(null);
	const [points, setPoints] = useState<PointsSummary | null>(null);
	const [err, setErr] = useState("");

	useEffect(() => {
		myChildren()
			.then((cs) => {
				setChildren(cs);
				if (cs.length) setSel(cs[0].student_id);
			})
			.catch((e) => setErr(String(e)));
	}, []);

	useEffect(() => {
		if (!sel) return;
		setErr("");
		Promise.all([childReport(sel), childPoints(sel)])
			.then(([r, p]) => {
				setReport(r);
				setPoints(p);
			})
			.catch((e) => setErr(String(e)));
	}, [sel]);

	return (
		<AppShell title="Cổng phụ huynh">
			<div className="flex gap-2 mb-4 items-center">
				<span className="text-sm text-neutral-500">Con:</span>
				<select
					value={sel}
					onChange={(e) => setSel(e.target.value)}
					data-testid="child-select"
					className="border rounded-lg px-2 py-1 text-sm bg-white dark:bg-neutral-900"
				>
					{children.map((c) => (
						<option key={c.student_id} value={c.student_id}>
							{c.full_name}
						</option>
					))}
				</select>
			</div>

			{err && <p className="text-danger text-sm mb-2">{err}</p>}

			{points && (
				<Card className="mb-4">
					<CardContent className="flex items-center gap-4 flex-wrap">
						<span
							className="text-2xl font-bold text-primary"
							data-testid="child-points"
						>
							{points.total} điểm
						</span>
						<span className="text-sm text-neutral-500">
							🔥 chuỗi {points.streak} ngày
						</span>
						<div className="flex gap-1 flex-wrap">
							{points.badges.map((b) => (
								<Chip key={b.code}>
									<ChipLabel>{b.name}</ChipLabel>
								</Chip>
							))}
						</div>
					</CardContent>
				</Card>
			)}

			{report && <StudentReportView report={report} />}
		</AppShell>
	);
}
