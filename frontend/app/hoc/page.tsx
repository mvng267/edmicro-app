"use client";

import { Button, Card, CardContent } from "@heroui/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageState } from "@/components/PageState";
import { myAssignments, type TodoItem } from "@/lib/api";
import { fmtDue, TODO_STATUS } from "@/lib/labels";

export default function TodoPage() {
	const [todos, setTodos] = useState<TodoItem[]>([]);
	const [err, setErr] = useState("");
	const [loading, setLoading] = useState(true);
	const router = useRouter();

	useEffect(() => {
		myAssignments()
			.then(setTodos)
			.catch((e) => setErr(String(e)))
			.finally(() => setLoading(false));
	}, []);

	return (
		<AppShell title="Việc cần làm">
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			<PageState
				loading={loading}
				empty={todos.length === 0}
				emptyText="Chưa có bài nào được giao. Chờ giáo viên giao bài nhé!"
			/>
			<ul data-testid="todo-list" className="flex flex-col gap-2">
				{todos.map((t) => (
					<li key={t.assignee_id}>
						<Card>
							<CardContent className="flex flex-row gap-3 items-center flex-wrap">
								<div className="flex flex-col">
									<span className="font-medium">{t.practice_name}</span>
									{t.due_at && (
										<span
											className={`text-xs ${
												t.status === "overdue"
													? "text-danger font-medium"
													: "text-neutral-500"
											}`}
										>
											Hạn nộp: {fmtDue(t.due_at)}
										</span>
									)}
								</div>
								<span
									className={`text-xs rounded-full px-2 py-1 ${(TODO_STATUS[t.status] ?? TODO_STATUS.not_opened).tone}`}
									data-status={t.status}
								>
									{(TODO_STATUS[t.status] ?? { label: t.status }).label}
								</span>
								{t.status !== "submitted" ? (
									<Button
										onPress={() => router.push(`/hoc/lam-bai/${t.assignee_id}`)}
										data-testid={`do-${t.assignee_id}`}
									>
										Làm bài
									</Button>
								) : (
									t.attempt_id && (
										<Button
											variant="ghost"
											onPress={() =>
												router.push(`/hoc/ket-qua/${t.attempt_id}`)
											}
											data-testid={`result-${t.assignee_id}`}
										>
											Xem kết quả
										</Button>
									)
								)}
							</CardContent>
						</Card>
					</li>
				))}
			</ul>
		</AppShell>
	);
}
