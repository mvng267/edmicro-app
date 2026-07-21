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
	createQuestion,
	listQuestions,
	publishQuestion,
	type QuestionRow,
} from "@/lib/api";

export default function ContentPage() {
	const [questions, setQuestions] = useState<QuestionRow[]>([]);
	const [skillFilter, setSkillFilter] = useState("");
	const [err, setErr] = useState("");

	// form state
	const [type, setType] = useState("mcq_single");
	const [prompt, setPrompt] = useState("");
	const [skill, setSkill] = useState("reading");
	const [options, setOptions] = useState(["", ""]);
	const [correct, setCorrect] = useState(0);
	const [blankAnswer, setBlankAnswer] = useState("");
	const [rubric, setRubric] = useState("");

	async function refresh() {
		setQuestions(await listQuestions({ skill: skillFilter || undefined }));
	}
	// biome-ignore lint/correctness/useExhaustiveDependencies: refresh phụ thuộc skillFilter
	useEffect(() => {
		refresh().catch((e) => setErr(String(e)));
	}, [skillFilter]);

	async function save(publish: boolean) {
		setErr("");
		try {
			let content: Record<string, unknown>;
			let answer_key: Record<string, unknown>;
			if (type === "mcq_single") {
				content = { prompt, options: options.filter((o) => o.trim()) };
				answer_key = { correct_index: correct };
			} else if (type === "writing") {
				content = { prompt, rubric };
				answer_key = {};
			} else {
				content = { prompt };
				answer_key = { blanks: [blankAnswer.split("|").map((s) => s.trim())] };
			}
			const { id } = await createQuestion({
				type,
				language: "en",
				skill,
				content,
				answer_key,
			});
			if (publish) await publishQuestion(id);
			setPrompt("");
			setOptions(["", ""]);
			setBlankAnswer("");
			setRubric("");
			await refresh();
		} catch (e) {
			setErr(String(e));
		}
	}

	return (
		<AppShell title="Ngân hàng câu hỏi">
			<Card className="mb-4">
				<CardContent className="flex flex-col gap-3">
					<div className="flex gap-2 items-center">
						<select
							data-testid="q-type"
							className="h-10 rounded-lg border px-2 bg-transparent"
							value={type}
							onChange={(e) => setType(e.target.value)}
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
						>
							<option value="reading">Đọc</option>
							<option value="listening">Nghe</option>
							<option value="writing">Viết</option>
							<option value="speaking">Nói</option>
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
					<div className="flex gap-2">
						<Button onPress={() => save(false)} data-testid="q-save-draft">
							Lưu nháp
						</Button>
						<Button onPress={() => save(true)} data-testid="q-publish">
							Xuất bản
						</Button>
					</div>
				</CardContent>
			</Card>

			{err && <p className="text-danger text-sm mb-2">{err}</p>}

			<div className="flex gap-2 mb-3">
				<select
					data-testid="filter-skill"
					className="h-9 rounded-lg border px-2 bg-transparent text-sm"
					value={skillFilter}
					onChange={(e) => setSkillFilter(e.target.value)}
				>
					<option value="">Tất cả kỹ năng</option>
					<option value="reading">Đọc</option>
					<option value="listening">Nghe</option>
					<option value="writing">Viết</option>
					<option value="speaking">Nói</option>
				</select>
			</div>

			<ul data-testid="q-list" className="flex flex-col gap-2">
				{questions.map((q) => (
					<li
						key={q.id}
						className="p-3 rounded-lg bg-white dark:bg-neutral-900 flex gap-2 items-center"
					>
						<Chip>
							<ChipLabel>{q.type}</ChipLabel>
						</Chip>
						<span className="font-medium text-sm">{q.prompt}</span>
						<span className="text-neutral-500 text-sm">{q.skill}</span>
						<Chip>
							<ChipLabel>{q.status}</ChipLabel>
						</Chip>
					</li>
				))}
			</ul>
		</AppShell>
	);
}
