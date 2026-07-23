"use client";

import { Button, Card, CardContent, Chip, ChipLabel } from "@heroui/react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
	type CourseDetail,
	completeLesson,
	myCourseDetail,
	myCourses,
	myPoints,
	type PointsSummary,
	type StudentCourse,
} from "@/lib/api";

export default function MyCoursesPage() {
	const [courses, setCourses] = useState<StudentCourse[]>([]);
	const [points, setPoints] = useState<PointsSummary | null>(null);
	const [openId, setOpenId] = useState("");
	const [detail, setDetail] = useState<CourseDetail | null>(null);
	const [err, setErr] = useState("");

	async function refresh() {
		setCourses(await myCourses());
		setPoints(await myPoints());
	}
	// biome-ignore lint/correctness/useExhaustiveDependencies: chỉ load 1 lần
	useEffect(() => {
		refresh().catch((e) => setErr(String(e)));
	}, []);

	async function open(id: string) {
		setOpenId(id);
		setDetail(await myCourseDetail(id));
	}
	async function done(lessonId: string) {
		await completeLesson(lessonId).catch((e) => setErr(String(e)));
		await open(openId);
		await refresh();
	}

	return (
		<AppShell title="Khóa học của tôi">
			{points && (
				<Card className="mb-4">
					<CardContent className="flex items-center gap-4 flex-wrap">
						<span
							className="text-2xl font-bold text-primary"
							data-testid="my-points"
						>
							{points.total} điểm
						</span>
						<span className="text-sm text-neutral-500" data-testid="my-streak">
							🔥 chuỗi {points.streak} ngày
						</span>
						<div className="flex gap-1 flex-wrap" data-testid="my-badges">
							{points.badges.map((b) => (
								<Chip key={b.code}>
									<ChipLabel>{b.name}</ChipLabel>
								</Chip>
							))}
						</div>
					</CardContent>
				</Card>
			)}

			{err && <p className="text-danger text-sm mb-2">{err}</p>}

			{courses.length === 0 ? (
				<p className="text-sm text-neutral-500">Chưa có khóa học nào.</p>
			) : (
				<ul data-testid="my-course-list" className="flex flex-col gap-2">
					{courses.map((c) => (
						<li key={c.id}>
							<Card data-testid={`mycourse-${c.id}`}>
								<CardContent className="flex flex-col gap-2">
									<div className="flex items-center gap-3">
										<span className="font-medium">{c.name}</span>
										<span
											className="text-sm text-neutral-500"
											data-testid={`progress-${c.id}`}
										>
											{c.done}/{c.total} bài · {c.progress}%
										</span>
										<Button
											variant="ghost"
											className="ml-auto"
											onPress={() => open(c.id)}
											data-testid={`open-${c.id}`}
										>
											Học
										</Button>
									</div>
									{openId === c.id && detail && (
										<div className="flex flex-col gap-2 border-t border-neutral-200 dark:border-neutral-800 pt-2">
											{detail.lessons.map((l) => (
												<div
													key={l.id}
													className="flex items-center gap-2 text-sm"
												>
													<span className="flex-1">
														{l.title}{" "}
														<span className="text-neutral-400">({l.kind})</span>
													</span>
													{l.done ? (
														<Chip color="success">
															<ChipLabel>Đã xong</ChipLabel>
														</Chip>
													) : (
														<Button
															onPress={() => done(l.id)}
															data-testid={`complete-${l.id}`}
														>
															Hoàn thành
														</Button>
													)}
												</div>
											))}
										</div>
									)}
								</CardContent>
							</Card>
						</li>
					))}
				</ul>
			)}
		</AppShell>
	);
}
