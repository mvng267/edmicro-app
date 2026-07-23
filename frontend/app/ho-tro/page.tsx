"use client";

import {
	Button,
	Card,
	CardContent,
	Chip,
	ChipLabel,
	Input,
} from "@heroui/react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
	addTicketComment,
	closeTicket,
	createTicket,
	getTicket,
	listTickets,
	type TicketDetail,
	type TicketRow,
} from "@/lib/api";

export default function SupportPage() {
	const [tickets, setTickets] = useState<TicketRow[]>([]);
	const [subject, setSubject] = useState("");
	const [body, setBody] = useState("");
	const [openId, setOpenId] = useState("");
	const [detail, setDetail] = useState<TicketDetail | null>(null);
	const [comment, setComment] = useState("");
	const [err, setErr] = useState("");

	async function refresh() {
		setTickets(await listTickets());
	}
	// biome-ignore lint/correctness/useExhaustiveDependencies: chỉ load 1 lần
	useEffect(() => {
		refresh().catch((e) => setErr(String(e)));
	}, []);

	async function create() {
		setErr("");
		if (!subject.trim()) {
			setErr("Nhập tiêu đề");
			return;
		}
		try {
			await createTicket(subject, body);
			setSubject("");
			setBody("");
			await refresh();
		} catch (e) {
			setErr(String(e));
		}
	}
	async function open(id: string) {
		setOpenId(id);
		setDetail(await getTicket(id));
	}
	async function sendComment() {
		if (!comment.trim()) return;
		await addTicketComment(openId, comment).catch((e) => setErr(String(e)));
		setComment("");
		await open(openId);
	}
	async function close() {
		await closeTicket(openId).catch((e) => setErr(String(e)));
		await open(openId);
		await refresh();
	}

	return (
		<AppShell title="Hỗ trợ">
			<Card className="mb-4">
				<CardContent className="flex flex-col gap-2">
					<Input
						aria-label="Tiêu đề"
						placeholder="Tiêu đề vấn đề"
						data-testid="ticket-subject"
						value={subject}
						onChange={(e) => setSubject(e.target.value)}
					/>
					<Input
						aria-label="Mô tả"
						placeholder="Mô tả chi tiết"
						data-testid="ticket-body"
						value={body}
						onChange={(e) => setBody(e.target.value)}
					/>
					<Button onPress={create} data-testid="create-ticket">
						Gửi yêu cầu
					</Button>
				</CardContent>
			</Card>

			{err && <p className="text-danger text-sm mb-2">{err}</p>}

			<ul data-testid="ticket-list" className="flex flex-col gap-2">
				{tickets.map((t) => (
					<li key={t.id}>
						<Card data-testid={`ticket-${t.id}`}>
							<CardContent className="flex flex-col gap-2">
								<div className="flex items-center gap-3">
									<span className="font-medium">{t.subject}</span>
									<Chip color={t.status === "closed" ? "success" : "warning"}>
										<ChipLabel>{t.status}</ChipLabel>
									</Chip>
									<Button
										variant="ghost"
										className="ml-auto"
										onPress={() => open(t.id)}
										data-testid={`open-${t.id}`}
									>
										Mở
									</Button>
								</div>

								{openId === t.id && detail && (
									<div className="flex flex-col gap-2 border-t border-neutral-200 dark:border-neutral-800 pt-2">
										<p className="text-sm text-neutral-500">{detail.body}</p>
										<ul className="flex flex-col gap-1" data-testid="comments">
											{detail.comments.map((c) => (
												<li
													key={c.id}
													className="text-sm bg-neutral-50 dark:bg-neutral-900 rounded p-2"
												>
													{c.body}
												</li>
											))}
										</ul>
										<div className="flex gap-2">
											<Input
												aria-label="Bình luận"
												placeholder="Thêm bình luận"
												className="flex-1"
												value={comment}
												onChange={(e) => setComment(e.target.value)}
												data-testid="comment-body"
											/>
											<Button onPress={sendComment} data-testid="send-comment">
												Gửi
											</Button>
											{detail.status !== "closed" && (
												<Button
													variant="ghost"
													onPress={close}
													data-testid="close-ticket"
												>
													Đóng
												</Button>
											)}
										</div>
									</div>
								)}
							</CardContent>
						</Card>
					</li>
				))}
			</ul>
		</AppShell>
	);
}
