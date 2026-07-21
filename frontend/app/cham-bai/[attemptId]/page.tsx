"use client";

import {
	Button,
	Card,
	CardContent,
	Chip,
	ChipLabel,
	Input,
} from "@heroui/react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
	finalizeAnswer,
	type ReviewDetail,
	type ReviewOpenItem,
	reviewDetail,
} from "@/lib/api";

export default function ReviewPage() {
	const params = useParams<{ attemptId: string }>();
	const router = useRouter();
	const [detail, setDetail] = useState<ReviewDetail | null>(null);
	const [err, setErr] = useState("");

	async function load() {
		setDetail(await reviewDetail(params.attemptId));
	}
	// biome-ignore lint/correctness/useExhaustiveDependencies: load chỉ phụ thuộc attemptId
	useEffect(() => {
		load().catch((e) => setErr(String(e)));
	}, [params.attemptId]);

	return (
		<AppShell title="Chốt điểm bài viết">
			<Button
				variant="ghost"
				onPress={() => router.push("/cham-bai")}
				data-testid="back-queue"
				className="mb-3"
			>
				← Về hàng đợi
			</Button>
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			<div className="flex flex-col gap-4">
				{detail?.items.map((it) => (
					<ReviewCard key={it.answer_id} item={it} onDone={load} />
				))}
			</div>
		</AppShell>
	);
}

function ReviewCard({
	item,
	onDone,
}: {
	item: ReviewOpenItem;
	onDone: () => Promise<void>;
}) {
	const [score, setScore] = useState(
		String(item.final_score ?? item.ai_score ?? ""),
	);
	const [feedback, setFeedback] = useState(item.ai_feedback ?? "");
	const [busy, setBusy] = useState(false);
	const [err, setErr] = useState("");

	async function confirm() {
		setErr("");
		const n = Number(score);
		if (Number.isNaN(n) || n < 0 || n > 1) {
			setErr("Điểm phải từ 0 đến 1");
			return;
		}
		setBusy(true);
		try {
			await finalizeAnswer(item.answer_id, n, feedback || undefined);
			await onDone();
		} catch (e) {
			setErr(String(e));
		} finally {
			setBusy(false);
		}
	}

	const done = item.grade_status === "finalized";
	return (
		<Card data-testid={`review-card-${item.sort_order}`}>
			<CardContent className="flex flex-col gap-3">
				<div className="flex items-center justify-between">
					<p className="font-medium">
						Câu {item.sort_order + 1}. {item.prompt}
					</p>
					<Chip color={done ? "success" : "warning"}>
						<ChipLabel>{done ? "Đã chốt" : "Chờ chốt"}</ChipLabel>
					</Chip>
				</div>
				{item.rubric && (
					<p className="text-xs text-neutral-500">Rubric: {item.rubric}</p>
				)}

				<div>
					<p className="text-xs text-neutral-500 mb-1">Bài làm học sinh</p>
					<p className="text-sm whitespace-pre-wrap bg-neutral-50 dark:bg-neutral-900 rounded p-2">
						{item.your_answer || "(bỏ trống)"}
					</p>
				</div>

				<div className="text-sm text-neutral-500">
					AI đề xuất:{" "}
					<span className="font-medium text-foreground">
						{item.ai_score ?? "—"}
					</span>
					{item.ai_confidence !== null &&
						` (độ tự tin ${Math.round(item.ai_confidence * 100)}%)`}
					{item.grade_status === "needs_manual" &&
						" — AI không chấm được, vui lòng chấm tay"}
				</div>
				{item.ai_feedback && item.grade_status !== "needs_manual" && (
					<p className="text-sm text-neutral-500 italic">{item.ai_feedback}</p>
				)}

				<div className="flex gap-2 items-center flex-wrap">
					<Input
						aria-label="Điểm chốt (0..1)"
						placeholder="Điểm 0..1"
						className="w-28"
						value={score}
						onChange={(e) => setScore(e.target.value)}
						data-testid={`final-score-${item.sort_order}`}
					/>
					<Input
						aria-label="Nhận xét"
						placeholder="Nhận xét cho học sinh"
						className="flex-1 min-w-40"
						value={feedback}
						onChange={(e) => setFeedback(e.target.value)}
						data-testid={`final-feedback-${item.sort_order}`}
					/>
					<Button
						onPress={confirm}
						isDisabled={busy}
						data-testid={`finalize-${item.sort_order}`}
					>
						{done ? "Cập nhật" : "Chốt điểm"}
					</Button>
				</div>
				{err && <p className="text-danger text-sm">{err}</p>}
			</CardContent>
		</Card>
	);
}
