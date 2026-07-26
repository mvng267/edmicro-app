"use client";

import {
	Button,
	Card,
	CardContent,
	Chip,
	ChipLabel,
	Input,
} from "@heroui/react";
import {
	ChevronDown,
	ChevronRight,
	Folder,
	FolderPlus,
	Headphones,
	Inbox,
	Library,
	Pencil,
	Sparkles,
	Trash2,
} from "lucide-react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { Pager, PageState } from "@/components/PageState";
import { toast } from "@/components/Toast";
import {
	aiGenerateQuestions,
	archiveQuestion,
	createFolder,
	createQuestion,
	deleteFolder,
	getQuestion,
	listFolders,
	listQuestions,
	moveQuestion,
	publishQuestion,
	type QFolder,
	type QuestionRow,
	renameFolder,
	updateQuestion,
	uploadMedia,
} from "@/lib/api";
import { Q_STATUS, Q_TYPE, SKILL_LABEL } from "@/lib/labels";

const PAGE_SIZE = 20;

// ── Cây thư mục (dựng từ danh sách phẳng) ─────────────────────
function FolderNode({
	folder,
	all,
	depth,
	selected,
	onSelect,
	onAdd,
	onRename,
	onDelete,
}: {
	folder: QFolder;
	all: QFolder[];
	depth: number;
	selected: string;
	onSelect: (id: string) => void;
	onAdd: (parent: string) => void;
	onRename: (f: QFolder) => void;
	onDelete: (f: QFolder) => void;
}) {
	const children = all.filter((f) => f.parent_id === folder.id);
	const [open, setOpen] = useState(true);
	const active = selected === folder.id;
	return (
		<div>
			<div
				className={`group flex items-center gap-1 rounded-lg px-2 py-1.5 text-sm cursor-pointer ${
					active
						? "bg-primary-100 dark:bg-primary-950 text-primary font-medium"
						: "hover:bg-neutral-100 dark:hover:bg-neutral-800"
				}`}
				style={{ paddingLeft: `${8 + depth * 14}px` }}
				data-testid={`folder-${folder.id}`}
			>
				<button
					type="button"
					className="w-4 text-neutral-400"
					onClick={() => setOpen(!open)}
					aria-label={open ? "Thu gọn" : "Mở rộng"}
				>
					{children.length > 0 ? (
						open ? (
							<ChevronDown size={13} />
						) : (
							<ChevronRight size={13} />
						)
					) : (
						<span className="inline-block w-3" />
					)}
				</button>
				<button
					type="button"
					className="flex-1 flex items-center gap-1.5 text-left min-w-0"
					onClick={() => onSelect(folder.id)}
				>
					<Folder size={14} className="shrink-0 text-warning-500" />
					<span className="truncate">{folder.name}</span>
				</button>
				<span className="text-xs text-neutral-400">{folder.n_questions}</span>
				<span className="hidden group-hover:flex gap-0.5">
					<button
						type="button"
						title="Thêm thư mục con"
						onClick={() => onAdd(folder.id)}
						data-testid={`folder-add-${folder.id}`}
					>
						<FolderPlus size={13} />
					</button>
					<button
						type="button"
						title="Đổi tên"
						onClick={() => onRename(folder)}
						data-testid={`folder-rename-${folder.id}`}
					>
						<Pencil size={13} />
					</button>
					<button
						type="button"
						title="Xóa (chỉ khi rỗng)"
						onClick={() => onDelete(folder)}
						data-testid={`folder-del-${folder.id}`}
					>
						<Trash2 size={13} className="text-danger" />
					</button>
				</span>
			</div>
			{open &&
				children.map((c) => (
					<FolderNode
						key={c.id}
						folder={c}
						all={all}
						depth={depth + 1}
						selected={selected}
						onSelect={onSelect}
						onAdd={onAdd}
						onRename={onRename}
						onDelete={onDelete}
					/>
				))}
		</div>
	);
}

export default function ContentPage() {
	// kho + bộ lọc
	const [questions, setQuestions] = useState<QuestionRow[]>([]);
	const [folders, setFolders] = useState<QFolder[]>([]);
	const [selFolder, setSelFolder] = useState("");
	const [skillFilter, setSkillFilter] = useState("");
	const [statusFilter, setStatusFilter] = useState("");
	const [search, setSearch] = useState("");
	const [page, setPage] = useState(0);
	const [loading, setLoading] = useState(true);
	const [err, setErr] = useState("");
	const [msg, setMsg] = useState("");

	// form soạn/sửa
	const [formOpen, setFormOpen] = useState(false);
	const [editingId, setEditingId] = useState<string | null>(null);
	const [editingExplanation, setEditingExplanation] = useState<string | null>(
		null,
	);
	const [type, setType] = useState("mcq_single");
	const [prompt, setPrompt] = useState("");
	const [skill, setSkill] = useState("reading");
	const [options, setOptions] = useState(["", ""]);
	const [correct, setCorrect] = useState(0);
	const [blankAnswer, setBlankAnswer] = useState("");
	const [rubric, setRubric] = useState("");
	const [audioFile, setAudioFile] = useState<File | null>(null);

	// AI sinh câu
	const [aiOpen, setAiOpen] = useState(false);
	const [aiTopic, setAiTopic] = useState("");
	const [aiType, setAiType] = useState("mcq_single");
	const [aiSkill, setAiSkill] = useState("reading");
	const [aiCount, setAiCount] = useState("5");
	const [aiBusy, setAiBusy] = useState(false);

	async function refreshFolders() {
		setFolders(await listFolders());
	}
	async function refresh() {
		setLoading(true);
		try {
			setQuestions(
				await listQuestions(
					{
						skill: skillFilter || undefined,
						status: statusFilter || undefined,
						folder_id: selFolder || undefined,
					},
					PAGE_SIZE,
					page * PAGE_SIZE,
				),
			);
		} finally {
			setLoading(false);
		}
	}
	// biome-ignore lint/correctness/useExhaustiveDependencies: refresh phụ thuộc bộ lọc/trang
	useEffect(() => {
		refresh().catch((e) => setErr(String(e)));
	}, [skillFilter, statusFilter, page, selFolder]);
	// biome-ignore lint/correctness/useExhaustiveDependencies: chỉ load 1 lần
	useEffect(() => {
		refreshFolders().catch(() => {});
	}, []);

	const shown = search
		? questions.filter((x) =>
				(x.prompt ?? "").toLowerCase().includes(search.toLowerCase()),
			)
		: questions;

	function resetForm() {
		setEditingId(null);
		setEditingExplanation(null);
		setPrompt("");
		setOptions(["", ""]);
		setBlankAnswer("");
		setRubric("");
		setAudioFile(null);
		setCorrect(0);
	}

	async function startEdit(qid: string) {
		setErr("");
		try {
			const d = await getQuestion(qid);
			setFormOpen(true);
			setEditingId(qid);
			setEditingExplanation(d.explanation);
			setType(d.type);
			setSkill(d.skill ?? "reading");
			setPrompt(d.content.prompt ?? "");
			setOptions(d.content.options ?? ["", ""]);
			setCorrect(d.answer_key?.correct_index ?? 0);
			setRubric(d.content.rubric ?? "");
			setBlankAnswer((d.answer_key?.blanks ?? [[""]])[0].join("|"));
			window.scrollTo({ top: 0, behavior: "smooth" });
		} catch (e) {
			setErr(String(e));
		}
	}

	function buildContent(): {
		content: Record<string, unknown>;
		answer_key: Record<string, unknown>;
	} {
		if (type === "mcq_single") {
			return {
				content: { prompt, options: options.filter((o) => o.trim()) },
				answer_key: { correct_index: correct },
			};
		}
		if (type === "writing") {
			return { content: { prompt, rubric }, answer_key: {} };
		}
		return {
			content: { prompt },
			answer_key: { blanks: [blankAnswer.split("|").map((s) => s.trim())] },
		};
	}

	async function save(publish: boolean) {
		setErr("");
		setMsg("");
		try {
			const { content, answer_key } = buildContent();
			if (audioFile) content.audio_key = (await uploadMedia(audioFile)).key;
			if (editingId) {
				// sửa → tạo phiên bản mới (bài đã giao giữ version cũ)
				await updateQuestion(editingId, {
					content,
					answer_key,
					explanation: editingExplanation,
				});
				if (publish) await publishQuestion(editingId);
				toast("Đã lưu phiên bản mới của câu hỏi");
			} else {
				const { id } = await createQuestion({
					type,
					language: "en",
					skill,
					folder_id: selFolder && selFolder !== "none" ? selFolder : undefined,
					content,
					answer_key,
				});
				if (publish) await publishQuestion(id);
				toast(publish ? "Đã tạo + xuất bản câu hỏi" : "Đã lưu nháp");
			}
			resetForm();
			await Promise.all([refresh(), refreshFolders()]);
		} catch (e) {
			setErr(String(e));
		}
	}

	async function aiGen() {
		setErr("");
		setMsg("");
		if (!aiTopic.trim()) {
			setErr("Nhập chủ đề cho AI");
			return;
		}
		setAiBusy(true);
		try {
			const r = await aiGenerateQuestions({
				topic: aiTopic,
				skill: aiSkill,
				qtype: aiType,
				count: Number(aiCount) || 5,
				folder_id: selFolder && selFolder !== "none" ? selFolder : undefined,
			});
			toast(`AI đã sinh ${r.created} câu (nháp) — duyệt rồi bấm Xuất bản`);
			setStatusFilter("draft");
			await Promise.all([refresh(), refreshFolders()]);
		} catch (e) {
			setErr(
				String(e).includes("503")
					? "AI chưa được cấu hình trên máy chủ"
					: `AI lỗi: ${e}`,
			);
		} finally {
			setAiBusy(false);
		}
	}

	// thao tác thư mục
	async function addFolder(parent: string | null) {
		const name = window.prompt("Tên thư mục:");
		if (!name?.trim()) return;
		await createFolder(name.trim(), parent).catch((e) => setErr(String(e)));
		await refreshFolders();
	}
	async function doRename(f: QFolder) {
		const name = window.prompt("Tên mới:", f.name);
		if (!name?.trim() || name === f.name) return;
		await renameFolder(f.id, name.trim()).catch((e) => setErr(String(e)));
		await refreshFolders();
	}
	async function doDelete(f: QFolder) {
		if (!window.confirm(`Xóa thư mục "${f.name}"? (chỉ xóa được khi rỗng)`))
			return;
		try {
			await deleteFolder(f.id);
			if (selFolder === f.id) setSelFolder("");
			await refreshFolders();
		} catch (e) {
			setErr(
				String(e).includes("folder_not_empty")
					? "Thư mục chưa rỗng — hãy chuyển hết câu hỏi/thư mục con ra trước"
					: String(e),
			);
		}
	}

	async function doMove(qid: string, folderId: string) {
		await moveQuestion(qid, folderId || null).catch((e) => setErr(String(e)));
		await Promise.all([refresh(), refreshFolders()]);
	}

	async function doPublish(qid: string) {
		await publishQuestion(qid)
			.then(() => toast("Đã xuất bản câu hỏi"))
			.catch((e) => setErr(String(e)));
		await refresh();
	}

	const roots = folders.filter((f) => !f.parent_id);
	const totalInFolders = folders.reduce((s, f) => s + f.n_questions, 0);

	return (
		<AppShell title="Ngân hàng câu hỏi">
			<div className="flex flex-col lg:flex-row gap-4 items-start">
				{/* ── Cột trái: cây thư mục ── */}
				<Card className="w-full lg:w-64 shrink-0">
					<CardContent className="flex flex-col gap-1 p-2">
						<div className="flex items-center justify-between px-2 pb-1">
							<span className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
								Thư mục
							</span>
							<button
								type="button"
								title="Thêm thư mục gốc"
								className="text-sm"
								onClick={() => addFolder(null)}
								data-testid="folder-add-root"
							>
								<FolderPlus size={16} />
							</button>
						</div>
						<button
							type="button"
							onClick={() => setSelFolder("")}
							className={`flex justify-between rounded-lg px-2 py-1.5 text-sm ${
								selFolder === ""
									? "bg-primary-100 dark:bg-primary-950 text-primary font-medium"
									: "hover:bg-neutral-100 dark:hover:bg-neutral-800"
							}`}
							data-testid="folder-all"
						>
							<span className="flex items-center gap-1.5">
								<Library size={14} /> Tất cả
							</span>
						</button>
						<button
							type="button"
							onClick={() => setSelFolder("none")}
							className={`flex justify-between rounded-lg px-2 py-1.5 text-sm ${
								selFolder === "none"
									? "bg-primary-100 dark:bg-primary-950 text-primary font-medium"
									: "hover:bg-neutral-100 dark:hover:bg-neutral-800"
							}`}
							data-testid="folder-none"
						>
							<span className="flex items-center gap-1.5">
								<Inbox size={14} /> Chưa phân loại
							</span>
						</button>
						{roots.map((f) => (
							<FolderNode
								key={f.id}
								folder={f}
								all={folders}
								depth={0}
								selected={selFolder}
								onSelect={setSelFolder}
								onAdd={(p) => addFolder(p)}
								onRename={doRename}
								onDelete={doDelete}
							/>
						))}
						{folders.length === 0 && (
							<p className="px-2 py-1 text-xs text-neutral-400">
								Chưa có thư mục — bấm nút + để tạo (VD: IELTS → Reading)
							</p>
						)}
						<p className="px-2 pt-2 text-[11px] text-neutral-400 border-t border-neutral-100 dark:border-neutral-800">
							{totalInFolders} câu trong thư mục
						</p>
					</CardContent>
				</Card>

				{/* ── Cột phải ── */}
				<div className="flex-1 w-full min-w-0 flex flex-col gap-3">
					{/* thanh hành động */}
					<div className="flex gap-2 flex-wrap">
						<Button
							onPress={() => {
								if (formOpen && editingId) resetForm();
								setFormOpen(!formOpen);
							}}
							data-testid="toggle-form"
						>
							{formOpen ? "− Đóng form" : "+ Soạn câu hỏi"}
						</Button>
						<Button
							variant="ghost"
							onPress={() => setAiOpen(!aiOpen)}
							data-testid="toggle-ai"
						>
							<span className="flex items-center gap-1.5">
								<Sparkles size={15} /> Sinh câu hỏi bằng AI
							</span>
						</Button>
					</div>

					{/* khối AI */}
					{aiOpen && (
						<Card>
							<CardContent className="flex flex-col gap-2">
								<p className="text-sm text-neutral-500">
									AI sinh câu hỏi <b>nháp</b> vào
									{selFolder && selFolder !== "none"
										? " thư mục đang chọn"
										: " kho (chưa phân loại)"}{" "}
									— bạn duyệt/sửa rồi xuất bản.
								</p>
								<div className="flex gap-2 flex-wrap items-end">
									<Input
										aria-label="Chủ đề"
										placeholder="Chủ đề (VD: Thì hiện tại đơn, Từ vựng du lịch…)"
										className="flex-1 min-w-52"
										value={aiTopic}
										onChange={(e) => setAiTopic(e.target.value)}
										data-testid="ai-topic"
									/>
									<select
										className="h-10 rounded-lg border px-2 bg-transparent text-sm"
										value={aiType}
										onChange={(e) => setAiType(e.target.value)}
										data-testid="ai-type"
									>
										<option value="mcq_single">Trắc nghiệm</option>
										<option value="fill_blank">Điền từ</option>
									</select>
									<select
										className="h-10 rounded-lg border px-2 bg-transparent text-sm"
										value={aiSkill}
										onChange={(e) => setAiSkill(e.target.value)}
									>
										{Object.entries(SKILL_LABEL).map(([v, l]) => (
											<option key={v} value={v}>
												{l}
											</option>
										))}
									</select>
									<Input
										aria-label="Số câu"
										className="w-20"
										value={aiCount}
										onChange={(e) => setAiCount(e.target.value)}
										data-testid="ai-count"
									/>
									<Button
										onPress={aiGen}
										isDisabled={aiBusy}
										data-testid="ai-generate"
									>
										{aiBusy ? "Đang sinh…" : "Sinh câu hỏi"}
									</Button>
								</div>
							</CardContent>
						</Card>
					)}

					{/* form soạn/sửa */}
					{formOpen && (
						<Card>
							<CardContent className="flex flex-col gap-3">
								{editingId && (
									<p className="text-sm rounded-lg px-3 py-2 bg-warning-100 dark:bg-warning-950 text-warning-700 dark:text-warning-400">
										<Pencil size={13} className="inline -mt-0.5 mr-1" />
										Đang sửa câu hỏi — lưu sẽ tạo <b>phiên bản mới</b> (bài đã
										giao giữ nguyên phiên bản cũ).{" "}
										<button
											type="button"
											className="underline"
											onClick={resetForm}
										>
											Hủy sửa
										</button>
									</p>
								)}
								<div className="flex gap-2 items-center flex-wrap">
									<select
										data-testid="q-type"
										className="h-10 rounded-lg border px-2 bg-transparent"
										value={type}
										onChange={(e) => setType(e.target.value)}
										disabled={!!editingId}
									>
										<option value="mcq_single">Trắc nghiệm 1 đáp án</option>
										<option value="fill_blank">Điền vào chỗ trống</option>
										<option value="writing">Viết (AI chấm → GV duyệt)</option>
									</select>
									<select
										data-testid="q-skill"
										className="h-10 rounded-lg border px-2 bg-transparent"
										value={skill}
										onChange={(e) => setSkill(e.target.value)}
										disabled={!!editingId}
									>
										{Object.entries(SKILL_LABEL).map(([v, l]) => (
											<option key={v} value={v}>
												{l}
											</option>
										))}
									</select>
								</div>
								<Input
									aria-label="Đề bài"
									placeholder={
										type === "fill_blank" ? "Dùng ___ cho chỗ trống" : "Đề bài"
									}
									data-testid="q-prompt"
									value={prompt}
									onChange={(e) => setPrompt(e.target.value)}
								/>
								{type === "mcq_single" ? (
									<div className="flex flex-col gap-2">
										{options.map((o, i) => (
											// biome-ignore lint/suspicious/noArrayIndexKey: option cố định theo vị trí
											<div key={i} className="flex gap-2 items-center">
												<input
													type="radio"
													name="correct"
													checked={correct === i}
													onChange={() => setCorrect(i)}
													data-testid={`q-correct-${i}`}
												/>
												<Input
													aria-label={`Đáp án ${i + 1}`}
													placeholder={`Đáp án ${i + 1}`}
													data-testid={`q-option-${i}`}
													value={o}
													onChange={(e) => {
														const next = [...options];
														next[i] = e.target.value;
														setOptions(next);
													}}
												/>
											</div>
										))}
										<Button
											variant="ghost"
											onPress={() => setOptions([...options, ""])}
											data-testid="q-add-option"
										>
											+ Thêm đáp án
										</Button>
									</div>
								) : type === "writing" ? (
									<Input
										aria-label="Rubric chấm"
										placeholder="Rubric / tiêu chí chấm (tuỳ chọn) — VD: IELTS Writing Task 2"
										data-testid="q-rubric"
										value={rubric}
										onChange={(e) => setRubric(e.target.value)}
									/>
								) : (
									<Input
										aria-label="Đáp án chỗ trống"
										placeholder="Đáp án đúng (nhiều đáp án cách nhau bởi |)"
										data-testid="q-blank"
										value={blankAnswer}
										onChange={(e) => setBlankAnswer(e.target.value)}
									/>
								)}
								<label className="text-sm flex items-center gap-2 text-neutral-600 dark:text-neutral-300">
									<Headphones size={14} className="shrink-0" />
									Audio (câu nghe, tuỳ chọn):
									<input
										type="file"
										accept="audio/*"
										data-testid="q-audio"
										onChange={(e) => setAudioFile(e.target.files?.[0] ?? null)}
										className="text-sm"
									/>
									{audioFile && (
										<span className="text-xs text-neutral-500">
											{audioFile.name}
										</span>
									)}
								</label>
								<div className="flex gap-2">
									<Button
										onPress={() => save(false)}
										data-testid="q-save-draft"
									>
										{editingId ? "Lưu phiên bản mới" : "Lưu nháp"}
									</Button>
									<Button onPress={() => save(true)} data-testid="q-publish">
										{editingId ? "Lưu + Xuất bản" : "Xuất bản"}
									</Button>
								</div>
							</CardContent>
						</Card>
					)}

					{err && <p className="text-danger text-sm">{err}</p>}
					{msg && (
						<p className="text-success-600 text-sm" data-testid="content-msg">
							{msg}
						</p>
					)}

					{/* bộ lọc */}
					<div className="flex gap-2 flex-wrap items-center">
						<select
							data-testid="filter-skill"
							className="h-9 rounded-lg border px-2 bg-transparent text-sm"
							value={skillFilter}
							onChange={(e) => {
								setSkillFilter(e.target.value);
								setPage(0);
							}}
						>
							<option value="">Tất cả kỹ năng</option>
							{Object.entries(SKILL_LABEL).map(([v, l]) => (
								<option key={v} value={v}>
									{l}
								</option>
							))}
						</select>
						<select
							data-testid="filter-status"
							className="h-9 rounded-lg border px-2 bg-transparent text-sm"
							value={statusFilter}
							onChange={(e) => {
								setStatusFilter(e.target.value);
								setPage(0);
							}}
						>
							<option value="">Mọi trạng thái</option>
							<option value="draft">Nháp</option>
							<option value="published">Đã xuất bản</option>
							<option value="archived">Đã lưu trữ</option>
						</select>
						<input
							placeholder="Tìm theo đề bài…"
							aria-label="Tìm câu hỏi"
							data-testid="q-search"
							value={search}
							onChange={(e) => setSearch(e.target.value)}
							className="h-9 rounded-lg border px-3 text-sm bg-transparent min-w-52"
						/>
						<span className="text-xs text-neutral-500">{shown.length} câu</span>
					</div>

					<PageState
						loading={loading}
						empty={shown.length === 0}
						emptyText="Không có câu hỏi nào khớp bộ lọc."
					/>
					<ul data-testid="q-list" className="flex flex-col gap-2">
						{shown.map((q) => (
							<li
								key={q.id}
								className="p-3 rounded-lg bg-white dark:bg-neutral-900 flex flex-row gap-2 items-center flex-wrap"
							>
								<Chip>
									<ChipLabel>{Q_TYPE[q.type] ?? q.type}</ChipLabel>
								</Chip>
								<span className="font-medium text-sm">{q.prompt}</span>
								<span className="text-neutral-500 text-sm">
									{SKILL_LABEL[q.skill ?? ""] ?? q.skill}
								</span>
								<Chip
									color={q.status === "published" ? "success" : undefined}
									data-qstatus={q.status}
								>
									<ChipLabel>{Q_STATUS[q.status] ?? q.status}</ChipLabel>
								</Chip>
								<span className="ml-auto flex gap-1 items-center">
									{q.status === "draft" && (
										<Button
											variant="ghost"
											onPress={() => doPublish(q.id)}
											data-testid={`pub-${q.id}`}
										>
											Xuất bản
										</Button>
									)}
									<Button
										variant="ghost"
										onPress={() => startEdit(q.id)}
										data-testid={`edit-${q.id}`}
									>
										Sửa
									</Button>
									<select
										title="Chuyển thư mục"
										className="h-8 rounded-lg border px-1 bg-transparent text-xs max-w-28"
										value={q.folder_id ?? ""}
										onChange={(e) => doMove(q.id, e.target.value)}
										data-testid={`move-${q.id}`}
									>
										<option value="">Chưa phân loại</option>
										{folders.map((f) => (
											<option key={f.id} value={f.id}>
												{f.name}
											</option>
										))}
									</select>
									{q.status !== "archived" && (
										<Button
											variant="ghost"
											onPress={() =>
												archiveQuestion(q.id)
													.then(() =>
														Promise.all([refresh(), refreshFolders()]),
													)
													.catch((e) => setErr(String(e)))
											}
											data-testid={`archive-${q.id}`}
										>
											Lưu trữ
										</Button>
									)}
								</span>
							</li>
						))}
					</ul>
					<Pager
						page={page}
						setPage={setPage}
						hasMore={questions.length === PAGE_SIZE}
					/>
				</div>
			</div>
		</AppShell>
	);
}
