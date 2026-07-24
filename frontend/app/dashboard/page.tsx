"use client";

import { Card, CardContent, Chip, ChipLabel } from "@heroui/react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
	apiMe,
	type Child,
	type GradingQueueItem,
	getUsage,
	gradingQueue,
	type Klass,
	listClasses,
	listTickets,
	type Me,
	myAssignments,
	myChildren,
	myCourses,
	myPoints,
	type PointsSummary,
	type StudentCourse,
	type TicketRow,
	type TodoItem,
	type Usage,
} from "@/lib/api";

const ROLE_LABEL: Record<string, string> = {
	owner: "Chủ trung tâm",
	manager: "NV quản lý học vụ",
	academic_head: "Tổ trưởng chuyên môn",
	it_admin: "IT trung tâm",
	teacher: "Giáo viên",
	assistant: "Trợ giảng",
	content_editor: "NV nội dung",
	support_agent: "NV hỗ trợ",
	student: "Học sinh",
	parent: "Phụ huynh",
	admin: "Admin hệ thống",
};

function Stat({
	label,
	value,
	hint,
	href,
	testid,
}: {
	label: string;
	value: string | number;
	hint?: string;
	href?: string;
	testid?: string;
}) {
	const body = (
		<Card className="h-full">
			<CardContent>
				<p className="text-sm text-neutral-500">{label}</p>
				<p className="text-2xl font-bold" data-testid={testid}>
					{value}
				</p>
				{hint && <p className="text-xs text-neutral-400 mt-1">{hint}</p>}
			</CardContent>
		</Card>
	);
	return href ? (
		<Link href={href} className="flex-1 min-w-44">
			{body}
		</Link>
	) : (
		<div className="flex-1 min-w-44">{body}</div>
	);
}

function Quick({ href, label }: { href: string; label: string }) {
	return (
		<Link
			href={href}
			className="px-3 py-2 rounded-lg text-sm bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800"
		>
			{label}
		</Link>
	);
}

export default function DashboardPage() {
	const [me, setMe] = useState<Me | null>(null);
	const [todos, setTodos] = useState<TodoItem[] | null>(null);
	const [points, setPoints] = useState<PointsSummary | null>(null);
	const [courses, setCourses] = useState<StudentCourse[] | null>(null);
	const [queue, setQueue] = useState<GradingQueueItem[] | null>(null);
	const [classes, setClasses] = useState<Klass[] | null>(null);
	const [usage, setUsage] = useState<Usage | null>(null);
	const [children, setChildren] = useState<Child[] | null>(null);
	const [tickets, setTickets] = useState<TicketRow[] | null>(null);

	useEffect(() => {
		if (!localStorage.getItem("access_token")) {
			window.location.href = "/login";
			return;
		}
		// Mỗi vai trò chỉ gọi API mình có quyền; cái nào 403 thì bỏ qua, không vỡ trang.
		const ok = <T,>(p: Promise<T>, set: (v: T) => void) => {
			p.then(set).catch(() => {});
		};
		apiMe()
			.then((m) => {
				setMe(m);
				if (m.role === "student") {
					ok(myAssignments(), setTodos);
					ok(myPoints(), setPoints);
					ok(myCourses(), setCourses);
				} else if (m.role === "parent") {
					ok(myChildren(), setChildren);
				} else {
					ok(gradingQueue(), setQueue);
					ok(listClasses(), setClasses);
					ok(getUsage(), setUsage);
					ok(listTickets(), setTickets);
				}
			})
			.catch(() => {
				window.location.href = "/login";
			});
	}, []);

	const pending = todos?.filter((t) => t.status !== "submitted").length ?? 0;

	return (
		<AppShell title="Tổng quan">
			<div className="flex items-center gap-2 mb-4">
				<span className="text-sm text-neutral-500">Xin chào,</span>
				<Chip>
					<ChipLabel data-testid="role">
						{me ? (ROLE_LABEL[me.role] ?? me.role) : "…"}
					</ChipLabel>
				</Chip>
				<span className="sr-only" data-testid="greeting">
					Đăng nhập thành công
				</span>
			</div>

			{/* ── Học sinh ─────────────────────────────── */}
			{me?.role === "student" && (
				<div className="flex flex-col gap-4" data-testid="dash-student">
					<div className="flex gap-3 flex-wrap">
						<Stat
							label="Bài chưa nộp"
							value={pending}
							hint="Bấm để vào làm bài"
							href="/hoc"
							testid="stat-pending"
						/>
						<Stat
							label="Điểm tích lũy"
							value={points?.total ?? "—"}
							hint={points ? `🔥 chuỗi ${points.streak} ngày` : undefined}
							href="/hoc/khoa-hoc"
						/>
						<Stat
							label="Tiến độ khóa học"
							value={courses?.length ? `${courses[0].progress}%` : "—"}
							hint={courses?.length ? courses[0].name : "Chưa có khóa học"}
							href="/hoc/khoa-hoc"
						/>
						<Stat
							label="Huy hiệu"
							value={points?.badges.length ?? 0}
							hint={points?.badges.map((b) => b.name).join(", ") || "Chưa có"}
						/>
					</div>
					<div className="flex gap-2 flex-wrap">
						<Quick href="/hoc" label="Việc cần làm" />
						<Quick href="/hoc/khoa-hoc" label="Khóa học của tôi" />
						<Quick href="/hoc/bao-cao" label="Báo cáo của tôi" />
						<Quick href="/thong-bao" label="Thông báo" />
					</div>
				</div>
			)}

			{/* ── Phụ huynh ────────────────────────────── */}
			{me?.role === "parent" && (
				<div className="flex flex-col gap-4" data-testid="dash-parent">
					<div className="flex gap-3 flex-wrap">
						<Stat
							label="Số con đang theo dõi"
							value={children?.length ?? "…"}
							href="/phu-huynh"
						/>
					</div>
					<div className="flex gap-2 flex-wrap">
						{children?.map((c) => (
							<Quick
								key={c.student_id}
								href="/phu-huynh"
								label={`Xem kết quả ${c.full_name}`}
							/>
						))}
					</div>
				</div>
			)}

			{/* ── Nhân sự trung tâm ────────────────────── */}
			{me && me.role !== "student" && me.role !== "parent" && (
				<div className="flex flex-col gap-4" data-testid="dash-staff">
					<div className="flex gap-3 flex-wrap">
						{queue !== null && (
							<Stat
								label="Bài chờ chấm"
								value={queue.length}
								hint="Bài viết cần chốt điểm"
								href="/cham-bai"
								testid="stat-queue"
							/>
						)}
						{classes !== null && (
							<Stat
								label="Lớp đang mở"
								value={classes.length}
								href="/bao-cao"
							/>
						)}
						{usage && (
							<>
								<Stat
									label="Học sinh"
									value={usage.students}
									href="/quan-tri/usage"
								/>
								<Stat
									label="Quota AI writing"
									value={`${usage.ai_writing.used}/${usage.ai_writing.limit}`}
									hint={`Kỳ ${usage.period}`}
									href="/quan-tri/usage"
								/>
							</>
						)}
						{tickets !== null && (
							<Stat
								label="Ticket đang mở"
								value={tickets.filter((t) => t.status === "open").length}
								href="/ho-tro"
							/>
						)}
					</div>
					<div className="flex gap-2 flex-wrap">
						<Quick href="/cham-bai" label="Chấm bài" />
						<Quick href="/bao-cao" label="Báo cáo lớp" />
						<Quick href="/lich-hoc" label="Điểm danh" />
						<Quick href="/practices" label="Giao bài luyện tập" />
						<Quick href="/exams" label="Đề thi" />
						<Quick href="/khoa-hoc" label="Khóa học" />
						<Quick href="/bang-xep-hang" label="Bảng xếp hạng" />
					</div>
				</div>
			)}
		</AppShell>
	);
}
