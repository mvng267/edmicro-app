"use client";

import { Button, Card, CardContent } from "@heroui/react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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
	const [saved, setSaved] = useState(false);
	const [err, setErr] = useState("");

	useEffect(() => {
		startAttempt(params.assigneeId)
			.then((r) => {
				setAttemptId(r.attempt_id);
				setQuestions(r.practice.questions);
			})
			.catch((e) => setErr(String(e)));
	}, [params.assigneeId]);

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

	async function submit() {
		try {
			await submitAttempt(attemptId);
			router.push("/hoc");
		} catch (e) {
			setErr(String(e));
		}
	}

	return (
		<div className="min-h-screen bg-neutral-100 dark:bg-neutral-950 p-4">
			<div className="max-w-lg mx-auto flex flex-col gap-4">
				<div className="flex items-center justify-between">
					<h1 className="text-lg font-semibold">Làm bài</h1>
					{saved && (
						<span className="text-success-600 text-sm" data-testid="saved">
							Đã lưu ✓
						</span>
					)}
				</div>
				{err && <p className="text-danger text-sm">{err}</p>}
				{questions.map((q, qi) => (
					<Card key={q.question_version_id}>
						<CardContent className="flex flex-col gap-2">
							<p className="font-medium">
								Câu {qi + 1}. {q.content.prompt}
							</p>
							{(q.content.options ?? []).map((opt, oi) => (
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
							))}
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
