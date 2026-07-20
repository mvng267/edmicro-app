"use client";

import { Card, CardContent } from "@heroui/react";
import Link from "next/link";

import type { StudentReport } from "@/lib/api";

export function StudentReportView({
	report,
	linkResults = false,
}: {
	report: StudentReport;
	linkResults?: boolean;
}) {
	const { summary, items } = report;
	return (
		<div className="flex flex-col gap-4">
			<div className="flex gap-3">
				<Card className="flex-1">
					<CardContent>
						<p className="text-sm text-neutral-500">Điểm trung bình</p>
						<p
							className="text-2xl font-bold text-primary"
							data-testid="avg-score"
						>
							{summary.avg_score ?? "—"}
						</p>
					</CardContent>
				</Card>
				<Card className="flex-1">
					<CardContent>
						<p className="text-sm text-neutral-500">Đã nộp / được giao</p>
						<p className="text-2xl font-bold" data-testid="submitted-count">
							{summary.submitted}/{summary.assigned}
						</p>
					</CardContent>
				</Card>
			</div>

			{items.length === 0 ? (
				<p className="text-sm text-neutral-500">Chưa có bài nào được nộp.</p>
			) : (
				<Card>
					<CardContent className="p-0 overflow-x-auto">
						<table className="w-full text-sm" data-testid="report-items">
							<thead>
								<tr className="text-left text-neutral-500 border-b border-neutral-200 dark:border-neutral-800">
									<th className="p-3">Bài</th>
									<th className="p-3">Điểm</th>
									<th className="p-3">Đúng</th>
									<th className="p-3">Nộp lúc</th>
								</tr>
							</thead>
							<tbody>
								{items.map((it) => (
									<tr
										key={it.attempt_id}
										className="border-b border-neutral-100 dark:border-neutral-800"
										data-testid={`item-${it.attempt_id}`}
									>
										<td className="p-3 font-medium">
											{linkResults ? (
												<Link
													href={`/hoc/ket-qua/${it.attempt_id}`}
													className="text-primary hover:underline"
												>
													{it.practice_name}
												</Link>
											) : (
												it.practice_name
											)}
										</td>
										<td className="p-3">{it.score}</td>
										<td className="p-3">
											{it.correct_count}/{it.total_count}
										</td>
										<td className="p-3 text-neutral-500">
											{it.submitted_at?.slice(0, 10)}
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</CardContent>
				</Card>
			)}
		</div>
	);
}
