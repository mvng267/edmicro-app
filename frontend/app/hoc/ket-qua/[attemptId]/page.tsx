"use client";

import { Button, Card, CardContent, Chip, ChipLabel } from "@heroui/react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { type AttemptResult, getResult } from "@/lib/api";

export default function ResultPage() {
	const params = useParams<{ attemptId: string }>();
	const router = useRouter();
	const [result, setResult] = useState<AttemptResult | null>(null);
	const [err, setErr] = useState("");

	useEffect(() => {
		getResult(params.attemptId)
			.then(setResult)
			.catch((e) => setErr(String(e)));
	}, [params.attemptId]);

	return (
		<div className="min-h-screen bg-neutral-100 dark:bg-neutral-950 p-4">
			<div className="max-w-lg mx-auto flex flex-col gap-4">
				<div className="flex items-center justify-between">
					<h1 className="text-lg font-semibold">Kết quả</h1>
					<Button
						variant="ghost"
						onPress={() => router.push("/hoc")}
						data-testid="back-hoc"
					>
						Về việc cần làm
					</Button>
				</div>
				{err && <p className="text-danger text-sm">{err}</p>}
				{result && (
					<>
						<Card>
							<CardContent className="flex items-center gap-4">
								<span
									className="text-3xl font-bold text-primary"
									data-testid="score"
								>
									{result.score}
								</span>
								<span className="text-sm text-neutral-500">
									Đúng {result.correct_count}/{result.total_count} câu
								</span>
								{result.is_exam && result.band && (
									<span
										className="ml-auto text-sm font-semibold rounded-lg px-3 py-1 bg-primary-100 dark:bg-primary-950 text-primary"
										data-testid="band"
									>
										Band {result.band}
									</span>
								)}
							</CardContent>
						</Card>
						{result.status === "provisional" && (
							<p
								className="text-sm text-warning-600"
								data-testid="provisional-banner"
							>
								Điểm tạm tính — câu tự luận đang chờ giáo viên duyệt.
							</p>
						)}
						{result.review.map((r) =>
							r.type === "writing" ? (
								<Card key={r.sort_order} data-testid={`review-${r.sort_order}`}>
									<CardContent className="flex flex-col gap-2">
										<div className="flex items-center justify-between">
											<p className="font-medium">
												Câu {r.sort_order + 1}. {r.content.prompt}
											</p>
											<Chip
												color={
													r.grade_status === "finalized" ? "success" : "warning"
												}
												data-testid={`verdict-${r.sort_order}`}
											>
												<ChipLabel>
													{r.grade_status === "finalized"
														? `Điểm ${r.final_score}`
														: "Chờ GV duyệt"}
												</ChipLabel>
											</Chip>
										</div>
										<p className="text-sm whitespace-pre-wrap bg-neutral-50 dark:bg-neutral-900 rounded p-2">
											{r.your_answer?.text || "(bỏ trống)"}
										</p>
										{r.grade_status === "finalized" && r.ai_feedback && (
											<p className="text-sm text-neutral-500 italic">
												Nhận xét: {r.ai_feedback}
											</p>
										)}
									</CardContent>
								</Card>
							) : (
								<Card key={r.sort_order} data-testid={`review-${r.sort_order}`}>
									<CardContent className="flex flex-col gap-2">
										<div className="flex items-center justify-between">
											<p className="font-medium">
												Câu {r.sort_order + 1}. {r.content.prompt}
											</p>
											<Chip
												color={r.is_correct ? "success" : "danger"}
												data-testid={`verdict-${r.sort_order}`}
											>
												<ChipLabel>{r.is_correct ? "Đúng" : "Sai"}</ChipLabel>
											</Chip>
										</div>
										{(r.content.options ?? []).map((opt, oi) => {
											const chosen = r.your_answer?.selected === oi;
											const correct = r.answer_key?.correct_index === oi;
											return (
												<div
													// biome-ignore lint/suspicious/noArrayIndexKey: option cố định theo vị trí
													key={oi}
													className={`text-sm px-2 py-1 rounded ${
														correct
															? "bg-success-100 dark:bg-success-950 font-medium"
															: chosen
																? "bg-danger-100 dark:bg-danger-950"
																: ""
													}`}
												>
													{opt}
													{correct && " ✓ (đáp án đúng)"}
													{chosen && !correct && " ✗ (bạn chọn)"}
												</div>
											);
										})}
										{r.explanation && (
											<p className="text-sm text-neutral-500 italic">
												{r.explanation}
											</p>
										)}
									</CardContent>
								</Card>
							),
						)}
					</>
				)}
			</div>
		</div>
	);
}
