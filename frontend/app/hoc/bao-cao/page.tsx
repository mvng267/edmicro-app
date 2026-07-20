"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { StudentReportView } from "@/components/StudentReportView";
import { myReport, type StudentReport } from "@/lib/api";

export default function MyReportPage() {
	const [report, setReport] = useState<StudentReport | null>(null);
	const [err, setErr] = useState("");

	useEffect(() => {
		myReport()
			.then(setReport)
			.catch((e) => setErr(String(e)));
	}, []);

	return (
		<AppShell title="Báo cáo của tôi">
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			{report && <StudentReportView report={report} linkResults />}
		</AppShell>
	);
}
