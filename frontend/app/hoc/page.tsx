"use client";

import { Button, Card, CardContent, Chip, ChipLabel } from "@heroui/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { myAssignments, type TodoItem } from "@/lib/api";

export default function TodoPage() {
	const [todos, setTodos] = useState<TodoItem[]>([]);
	const [err, setErr] = useState("");
	const router = useRouter();

	useEffect(() => {
		myAssignments()
			.then(setTodos)
			.catch((e) => setErr(String(e)));
	}, []);

	return (
		<AppShell title="Việc cần làm">
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			<ul data-testid="todo-list" className="flex flex-col gap-2">
				{todos.map((t) => (
					<li key={t.assignee_id}>
						<Card>
							<CardContent className="flex gap-3 items-center">
								<span className="font-medium">{t.practice_name}</span>
								<Chip>
									<ChipLabel>{t.status}</ChipLabel>
								</Chip>
								{t.status !== "submitted" && (
									<Button
										onPress={() => router.push(`/hoc/lam-bai/${t.assignee_id}`)}
										data-testid={`do-${t.assignee_id}`}
									>
										Làm bài
									</Button>
								)}
							</CardContent>
						</Card>
					</li>
				))}
			</ul>
		</AppShell>
	);
}
