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
	addLesson,
	assignCourse,
	type CourseDetail,
	type CourseRow,
	createCourse,
	getCourse,
	type Klass,
	listClasses,
	listCourses,
} from "@/lib/api";

export default function CoursesAdminPage() {
	const [courses, setCourses] = useState<CourseRow[]>([]);
	const [classes, setClasses] = useState<Klass[]>([]);
	const [name, setName] = useState("");
	const [openId, setOpenId] = useState("");
	const [detail, setDetail] = useState<CourseDetail | null>(null);
	const [lessonTitle, setLessonTitle] = useState("");
	const [lessonKind, setLessonKind] = useState("text");
	const [assignClass, setAssignClass] = useState("");
	const [err, setErr] = useState("");
	const [msg, setMsg] = useState("");

	async function refresh() {
		setCourses(await listCourses());
		setClasses(await listClasses());
	}
	// biome-ignore lint/correctness/useExhaustiveDependencies: chỉ load 1 lần
	useEffect(() => {
		refresh().catch((e) => setErr(String(e)));
	}, []);

	async function open(id: string) {
		setOpenId(id);
		setDetail(await getCourse(id));
	}
	async function newCourse() {
		setErr("");
		try {
			await createCourse(name);
			setName("");
			await refresh();
			setMsg("Đã tạo khóa học");
		} catch (e) {
			setErr(String(e));
		}
	}
	async function newLesson() {
		setErr("");
		try {
			await addLesson(openId, { title: lessonTitle, kind: lessonKind });
			setLessonTitle("");
			await open(openId);
			await refresh();
		} catch (e) {
			setErr(String(e));
		}
	}
	async function assign() {
		setErr("");
		const cid = assignClass || classes[classes.length - 1]?.id;
		if (!cid) {
			setErr("Chưa có lớp");
			return;
		}
		try {
			await assignCourse(openId, cid);
			setMsg("Đã giao khóa cho lớp");
		} catch (e) {
			setErr(String(e));
		}
	}

	return (
		<AppShell title="Khóa học">
			<Card className="mb-4">
				<CardContent className="flex gap-2 items-center">
					<Input
						aria-label="Tên khóa học"
						placeholder="Tên khóa học"
						data-testid="course-name"
						value={name}
						onChange={(e) => setName(e.target.value)}
					/>
					<Button onPress={newCourse} data-testid="add-course">
						Tạo khóa
					</Button>
				</CardContent>
			</Card>

			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			{msg && <p className="text-success-600 text-sm mb-2">{msg}</p>}

			<ul data-testid="course-list" className="flex flex-col gap-2">
				{courses.map((c) => (
					<li key={c.id}>
						<Card data-testid={`course-${c.id}`}>
							<CardContent className="flex flex-col gap-2">
								<div className="flex items-center gap-3">
									<span className="font-medium">{c.name}</span>
									<span className="text-sm text-neutral-500">
										{c.n_lessons} bài
									</span>
									<Button
										variant="ghost"
										className="ml-auto"
										onPress={() => open(c.id)}
										data-testid={`open-${c.id}`}
									>
										Quản lý
									</Button>
								</div>

								{openId === c.id && detail && (
									<div className="flex flex-col gap-2 border-t border-neutral-200 dark:border-neutral-800 pt-2">
										<ol className="text-sm list-decimal pl-5">
											{detail.lessons.map((l) => (
												<li key={l.id}>
													{l.title}{" "}
													<Chip>
														<ChipLabel>{l.kind}</ChipLabel>
													</Chip>
												</li>
											))}
										</ol>
										<div className="flex gap-2 items-center flex-wrap">
											<Input
												aria-label="Tên bài học"
												placeholder="Tên bài học"
												className="min-w-40"
												value={lessonTitle}
												onChange={(e) => setLessonTitle(e.target.value)}
												data-testid="lesson-title"
											/>
											<select
												value={lessonKind}
												onChange={(e) => setLessonKind(e.target.value)}
												data-testid="lesson-kind"
												className="border rounded-lg px-2 py-1 text-sm bg-white dark:bg-neutral-900"
											>
												<option value="text">Văn bản</option>
												<option value="video">Video</option>
												<option value="file">Tài liệu</option>
												<option value="flashcard">Flashcard</option>
											</select>
											<Button onPress={newLesson} data-testid="add-lesson">
												Thêm bài
											</Button>
										</div>
										<div className="flex gap-2 items-center">
											<span className="text-sm text-neutral-500">
												Giao lớp:
											</span>
											<select
												value={assignClass}
												onChange={(e) => setAssignClass(e.target.value)}
												data-testid="assign-class"
												className="border rounded-lg px-2 py-1 text-sm bg-white dark:bg-neutral-900"
											>
												<option value="">Lớp mới nhất</option>
												{classes.map((cl) => (
													<option key={cl.id} value={cl.id}>
														{cl.name}
													</option>
												))}
											</select>
											<Button onPress={assign} data-testid="assign-course">
												Giao khóa
											</Button>
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
