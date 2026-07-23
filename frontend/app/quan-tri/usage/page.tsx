"use client";

import { Card, CardContent } from "@heroui/react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { getUsage, type Usage } from "@/lib/api";

function Stat({ label, value }: { label: string; value: string | number }) {
	return (
		<Card className="flex-1 min-w-40">
			<CardContent>
				<p className="text-sm text-neutral-500">{label}</p>
				<p className="text-2xl font-bold">{value}</p>
			</CardContent>
		</Card>
	);
}

export default function UsagePage() {
	const [u, setU] = useState<Usage | null>(null);
	const [err, setErr] = useState("");

	useEffect(() => {
		getUsage()
			.then(setU)
			.catch((e) => setErr(String(e)));
	}, []);

	return (
		<AppShell title="Mức dùng & hạn mức">
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			{u && (
				<div className="flex flex-col gap-4" data-testid="usage">
					<div className="flex gap-3 flex-wrap">
						<Stat label="Học sinh" value={u.students} />
						<Stat label="Lớp học" value={u.classes} />
						<Stat label="Lượt nộp bài" value={u.submissions} />
						<Stat label="Khóa học" value={u.courses} />
					</div>
					<Card>
						<CardContent>
							<p className="text-sm text-neutral-500 mb-1">
								Hạn mức chấm AI writing ({u.period})
							</p>
							<p className="text-2xl font-bold text-primary">
								{u.ai_writing.used}/{u.ai_writing.limit}
							</p>
							<div className="mt-2 h-2 rounded-full bg-neutral-200 dark:bg-neutral-800 overflow-hidden">
								<div
									className="h-full bg-primary"
									style={{
										width: `${
											u.ai_writing.limit
												? Math.min(
														100,
														(u.ai_writing.used / u.ai_writing.limit) * 100,
													)
												: 0
										}%`,
									}}
								/>
							</div>
						</CardContent>
					</Card>
				</div>
			)}
		</AppShell>
	);
}
