"use client";

import { Button } from "@heroui/react";
import { FileDown } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { StudentReportView } from "@/components/StudentReportView";
import { downloadPdf, type StudentReport, studentReport } from "@/lib/api";

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
			<div className="flex gap-2 mb-3">
				<Button
					variant="ghost"
					onPress={() => router.push("/bao-cao")}
					data-testid="back-class"
				>
					← Về báo cáo lớp
				</Button>
				<Button
					variant="ghost"
					onPress={() =>
						downloadPdf(
							`/api/v1/reports/students/${params.studentId}/pdf`,
							"bao-cao-hoc-tap.pdf",
						).catch(() => {})
					}
					data-testid="student-pdf"
				>
					<span className="flex items-center gap-1.5">
						<FileDown size={15} /> Tải phiếu PDF gửi phụ huynh
					</span>
				</Button>
			</div>
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			{report && <StudentReportView report={report} />}
		</AppShell>
	);
}
