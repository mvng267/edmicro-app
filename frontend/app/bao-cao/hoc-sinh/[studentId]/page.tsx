"use client";

import { Button } from "@heroui/react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { StudentReportView } from "@/components/StudentReportView";
import { type StudentReport, studentReport } from "@/lib/api";

export default function StudentReportPage() {
	const params = useParams<{ studentId: string }>();
	const router = useRouter();
	const [report, setReport] = useState<StudentReport | null>(null);
	const [err, setErr] = useState("");

	useEffect(() => {
		studentReport(params.studentId)
			.then(setReport)
			.catch((e) => setErr(String(e)));
	}, [params.studentId]);

	return (
		<AppShell title="Báo cáo học sinh">
			<Button
				variant="ghost"
				onPress={() => router.push("/bao-cao")}
				data-testid="back-class"
				className="mb-3"
			>
				← Về báo cáo lớp
			</Button>
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			{report && <StudentReportView report={report} />}
		</AppShell>
	);
}
