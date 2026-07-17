"use client";

import {
	Alert,
	AlertDescription,
	Button,
	Card,
	CardContent,
	Chip,
	ChipLabel,
} from "@heroui/react";
import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
	type Credential,
	type ImportPreview,
	importCommit,
	importValidate,
} from "@/lib/api";

export default function ImportPage() {
	const [preview, setPreview] = useState<ImportPreview | null>(null);
	const [creds, setCreds] = useState<Credential[] | null>(null);
	const [err, setErr] = useState("");

	async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
		setErr("");
		setCreds(null);
		const f = e.target.files?.[0];
		if (!f) return;
		try {
			setPreview(await importValidate(f));
		} catch (e2) {
			setErr(String(e2));
		}
	}

	async function commit() {
		if (!preview) return;
		try {
			const r = await importCommit(preview.job_id);
			setCreds(r.credentials);
		} catch (e2) {
			setErr(String(e2));
		}
	}

	function downloadCsv() {
		if (!creds) return;
		const csv = `username,password,full_name\n${creds
			.map((c) => `${c.username},${c.password},${c.full_name}`)
			.join("\n")}`;
		const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
		const a = document.createElement("a");
		a.href = url;
		a.download = "tai-khoan.csv";
		a.click();
	}

	return (
		<AppShell title="Import học sinh từ Excel">
			<Card className="mb-4">
				<CardContent className="flex flex-col gap-3">
					<input
						type="file"
						accept=".xlsx"
						onChange={onFile}
						data-testid="import-file"
					/>
					{preview && (
						<div className="flex gap-2">
							<Chip>
								<ChipLabel>{preview.summary.valid} hợp lệ</ChipLabel>
							</Chip>
							<Chip>
								<ChipLabel>{preview.summary.errors} lỗi</ChipLabel>
							</Chip>
							<Button onPress={commit} data-testid="import-commit">
								Bỏ qua lỗi, tạo {preview.summary.valid} tài khoản
							</Button>
						</div>
					)}
				</CardContent>
			</Card>

			{err && <p className="text-danger text-sm mb-2">{err}</p>}

			{preview && !creds && (
				<ul data-testid="preview-rows" className="flex flex-col gap-1 text-sm">
					{preview.rows.map((r) => (
						<li
							key={r.row_no}
							className={`p-2 rounded ${r.error ? "bg-danger-50 text-danger-600" : "bg-white dark:bg-neutral-900"}`}
						>
							#{r.row_no} {r.data.full_name ?? "(trống)"}{" "}
							{r.error && `— ${r.error}`}
						</li>
					))}
				</ul>
			)}

			{creds && (
				<Alert status="success" data-testid="import-result">
					<AlertDescription>
						Đã tạo {creds.length} tài khoản.{" "}
						<button type="button" onClick={downloadCsv} className="underline">
							Tải danh sách (CSV)
						</button>
					</AlertDescription>
				</Alert>
			)}
		</AppShell>
	);
}
