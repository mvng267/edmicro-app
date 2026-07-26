"use client";

import { Button } from "@heroui/react";
import { FileDown } from "lucide-react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { StudentReportView } from "@/components/StudentReportView";
import { downloadPdf, myReport, type StudentReport } from "@/lib/api";

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
			<div className="flex justify-end mb-3">
				<Button
					variant="ghost"
					onPress={() =>
						downloadPdf("/api/v1/me/report/pdf", "bao-cao-cua-toi.pdf").catch(
							() => {},
						)
					}
					data-testid="my-pdf"
				>
					<span className="flex items-center gap-1.5">
						<FileDown size={15} /> Tải phiếu PDF
					</span>
				</Button>
			</div>
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			{report && <StudentReportView report={report} linkResults />}
		</AppShell>
	);
}
