"use client";

import { Button, Card, CardContent } from "@heroui/react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import {
	type AttemptQuestion,
	saveAnswer,
	startAttempt,
	submitAttempt,
} from "@/lib/api";

export default function DoPracticePage() {
	const params = useParams<{ assigneeId: string }>();
	const router = useRouter();
	const [attemptId, setAttemptId] = useState("");
	const [questions, setQuestions] = useState<AttemptQuestion[]>([]);
	const [answers, setAnswers] = useState<Record<string, number>>({});
	const [texts, setTexts] = useState<Record<string, string>>({});
	const [saved, setSaved] = useState(false);
	const [err, setErr] = useState("");
	const [deadline, setDeadline] = useState<number | null>(null);
	const [remaining, setRemaining] = useState<number | null>(null);
	const submittingRef = useRef(false);

	useEffect(() => {
		startAttempt(params.assigneeId)
			.then((r) => {
				setAttemptId(r.attempt_id);
				setQuestions(r.practice.questions);
				if (r.deadline_at) setDeadline(new Date(r.deadline_at).getTime());
			})
			.catch((e) => setErr(String(e)));
	}, [params.assigneeId]);

	// đồng hồ đề thi: đếm ngược theo deadline server; hết giờ tự nộp
	// biome-ignore lint/correctness/useExhaustiveDependencies: chỉ chạy khi có deadline+attempt
	useEffect(() => {
		if (deadline === null || !attemptId) return;
		const tick = () => {
			const rem = Math.max(0, Math.round((deadline - Date.now()) / 1000));
			setRemaining(rem);
			if (rem <= 0) {
				clearInterval(id);
				submit();
			}
		};
		tick();
		const id = setInterval(tick, 1000);
		return () => clearInterval(id);
	}, [deadline, attemptId]);

	async function choose(qv: string, idx: number) {
		setAnswers((a) => ({ ...a, [qv]: idx }));
		setSaved(false);
		try {
			await saveAnswer(attemptId, qv, { selected: idx });
			setSaved(true);
		} catch (e) {
			setErr(String(e));
		}
	}

	async function write(qv: string, value: string) {
		setTexts((t) => ({ ...t, [qv]: value }));
		setSaved(false);
		try {
			await saveAnswer(attemptId, qv, { text: value });
			setSaved(true);
		} catch (e) {
			setErr(String(e));
		}
	}

	async function submit() {
		if (submittingRef.current) return;
		submittingRef.current = true;
		try {
			await submitAttempt(attemptId);
			router.push(`/hoc/ket-qua/${attemptId}`);
		} catch (e) {
			submittingRef.current = false;
			setErr(String(e));
		}
	}

	function fmt(sec: number) {
		const m = Math.floor(sec / 60);
		const s = sec % 60;
		return `${m}:${String(s).padStart(2, "0")}`;
	}

	return (
		<div className="min-h-screen bg-neutral-100 dark:bg-neutral-950 p-4">
			<div className="max-w-lg mx-auto flex flex-col gap-4">
				<div className="flex items-center justify-between">
					<h1 className="text-lg font-semibold">Làm bài</h1>
					<div className="flex items-center gap-3">
						{remaining !== null && (
							<span
								className={`text-sm font-mono font-semibold ${
									remaining <= 60
										? "text-danger"
										: "text-neutral-600 dark:text-neutral-300"
								}`}
								data-testid="exam-timer"
							>
								⏱ {fmt(remaining)}
							</span>
						)}
						{saved && (
							<span className="text-success-600 text-sm" data-testid="saved">
								Đã lưu ✓
							</span>
						)}
					</div>
				</div>
				{err && <p className="text-danger text-sm">{err}</p>}
				{questions.map((q, qi) => (
					<Card key={q.question_version_id}>
						<CardContent className="flex flex-col gap-2">
							<p className="font-medium">
								Câu {qi + 1}. {q.content.prompt}
							</p>
							{q.type === "writing" ? (
								<textarea
									className="min-h-32 rounded-lg border p-2 text-sm bg-white dark:bg-neutral-900"
									placeholder="Viết bài của bạn ở đây…"
									value={texts[q.question_version_id] ?? ""}
									onChange={(e) => write(q.question_version_id, e.target.value)}
									data-testid={`write-${qi}`}
								/>
							) : (
								(q.content.options ?? []).map((opt, oi) => (
									// biome-ignore lint/suspicious/noArrayIndexKey: option cố định theo vị trí
									<label key={oi} className="flex gap-2 items-center text-sm">
										<input
											type="radio"
											name={q.question_version_id}
											checked={answers[q.question_version_id] === oi}
											onChange={() => choose(q.question_version_id, oi)}
											data-testid={`ans-${qi}-${oi}`}
										/>
										{opt}
									</label>
								))
							)}
						</CardContent>
					</Card>
				))}
				<Button onPress={submit} data-testid="submit-attempt">
					Nộp bài
				</Button>
			</div>
		</div>
	);
}
