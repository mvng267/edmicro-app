"use client";

import { Card, CardContent, Chip, ChipLabel } from "@heroui/react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageState } from "@/components/PageState";
import { type GradingQueueItem, gradingQueue } from "@/lib/api";

export default function GradingQueuePage() {
	const [items, setItems] = useState<GradingQueueItem[]>([]);
	const [err, setErr] = useState("");
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		gradingQueue()
			.then(setItems)
			.catch((e) => setErr(String(e)))
			.finally(() => setLoading(false));
	}, []);

	return (
		<AppShell title="Chấm bài (hàng đợi)">
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			<PageState
				loading={loading}
				empty={items.length === 0}
				emptyText="Không có bài nào chờ chấm. 🎉"
			/>
			{items.length === 0 ? null : (
				<ul data-testid="grading-queue" className="flex flex-col gap-2">
					{items.map((it) => (
						<li key={it.attempt_id}>
							<Link href={`/cham-bai/${it.attempt_id}`}>
								<Card>
									<CardContent className="flex gap-3 items-center">
										<span className="font-medium">{it.student_name}</span>
										<span className="text-sm text-neutral-500">
											{it.practice_name} · {it.class_name}
										</span>
										<Chip>
											<ChipLabel>{it.pending_count} câu</ChipLabel>
										</Chip>
										{it.has_manual && (
											<Chip color="danger">
												<ChipLabel>AI lỗi/hết hạn mức — chấm tay</ChipLabel>
											</Chip>
										)}
									</CardContent>
								</Card>
							</Link>
						</li>
					))}
				</ul>
			)}
		</AppShell>
	);
}
