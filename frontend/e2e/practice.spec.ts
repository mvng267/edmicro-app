import { expect, test } from "@playwright/test";

// M3: owner dựng lớp + HS(trong lớp) + câu hỏi → practice → giao; HS làm bài (autosave) → nộp.
test("giao bài practice, học sinh làm và nộp", async ({ page }) => {
	const stamp = Date.now().toString().slice(-6);

	// owner login
	await page.goto("/login");
	await page.getByLabel("Tên đăng nhập").fill("owner");
	await page.getByLabel("Mật khẩu").fill("owner123");
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/dashboard/);

	// chi nhánh + lớp
	await page.goto("/org/branches");
	await page.getByTestId("branch-name").fill(`CN ${stamp}`);
	await page.getByTestId("add-branch").click();
	await expect(page.getByTestId("branch-list")).toContainText(`CN ${stamp}`);

	await page.goto("/org/classes");
	await page
		.getByTestId("branch-select")
		.selectOption({ label: `CN ${stamp}` });
	await page.getByTestId("class-name").fill(`Lớp ${stamp}`);
	await page.getByTestId("add-class").click();
	await expect(page.getByTestId("class-list")).toContainText(`Lớp ${stamp}`);

	// học sinh TRONG lớp (lấy mật khẩu)
	await page.goto("/org/users");
	await page.getByTestId("user-name").fill(`HS ${stamp}`);
	await page.getByTestId("role-select").selectOption("student");
	await page.getByTestId("user-class").selectOption({ label: `Lớp ${stamp}` });
	await page.getByTestId("add-user").click();
	await expect(page.getByTestId("cred-box")).toBeVisible();
	const username =
		(await page.getByTestId("cred-username").textContent())?.trim() ?? "";
	const password =
		(await page.getByTestId("cred-password").textContent())?.trim() ?? "";

	// câu hỏi publish
	await page.goto("/content");
	await page.getByTestId("q-type").selectOption("mcq_single");
	await page.getByTestId("q-prompt").fill(`Câu ${stamp}?`);
	await page.getByTestId("q-option-0").fill("Đáp án A");
	await page.getByTestId("q-option-1").fill("Đáp án B");
	await page.getByTestId("q-correct-0").check();
	await page.getByTestId("q-publish").click();
	await expect(page.getByTestId("q-list")).toContainText("published");

	// practice + giao cho lớp
	await page.goto("/practices");
	await page.getByTestId("practice-name").fill(`Bài ${stamp}`);
	// chọn ĐÚNG câu vừa tạo (không .first() vì DB dev còn câu của test khác)
	await page
		.getByTestId("pick-list")
		.locator("li")
		.filter({ hasText: `Câu ${stamp}?` })
		.locator("input[type=checkbox]")
		.check();
	await page.getByTestId("save-practice").click();
	const row = page
		.getByTestId("practice-list")
		.locator("li")
		.filter({ hasText: `Bài ${stamp}` })
		.first();
	await expect(row).toBeVisible();
	await page
		.getByTestId("assign-class")
		.selectOption({ label: `Lớp ${stamp}` });
	await row.getByRole("button", { name: "Giao cho lớp" }).click();
	await expect(page.getByText(/Đã giao cho \d+ học sinh/)).toBeVisible();

	// logout → HS login
	await page.getByTestId("logout").click();
	await expect(page).toHaveURL(/\/login/);
	await page.waitForLoadState("networkidle");
	const u = page.getByLabel("Tên đăng nhập");
	await u.fill(username);
	await expect(u).toHaveValue(username);
	await page.getByLabel("Mật khẩu").fill(password);
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/dashboard/);

	// việc cần làm → làm bài
	await page.goto("/hoc");
	await expect(page.getByTestId("todo-list")).toContainText(`Bài ${stamp}`);
	await page
		.getByTestId("todo-list")
		.getByRole("button", { name: "Làm bài" })
		.click();
	await expect(page).toHaveURL(/\/hoc\/lam-bai\//);

	// chọn đáp án ĐÚNG (option 0) → thấy "Đã lưu" (autosave) → nộp
	await page.getByTestId("ans-0-0").check();
	await expect(page.getByTestId("saved")).toBeVisible();
	await page.getByTestId("submit-attempt").click();

	// tự động chấm → trang kết quả: điểm 100, câu 1 Đúng, lộ đáp án đúng
	await expect(page).toHaveURL(/\/hoc\/ket-qua\//);
	await expect(page.getByTestId("score")).toHaveText("100");
	await expect(page.getByTestId("verdict-0")).toContainText("Đúng");
	await expect(page.getByTestId("review-0")).toContainText("đáp án đúng");

	// quay lại việc cần làm: trạng thái submitted + có nút Xem kết quả
	await page.getByTestId("back-hoc").click();
	await expect(page).toHaveURL(/\/hoc$/);
	await expect(page.getByTestId("todo-list")).toContainText("submitted");
	await expect(
		page.getByTestId("todo-list").getByRole("button", { name: "Xem kết quả" }),
	).toBeVisible();

	// HS xem BÁO CÁO CỦA MÌNH: điểm TB 100 + có bài vừa làm
	await page.goto("/hoc/bao-cao");
	await expect(page.getByTestId("avg-score")).toHaveText("100");
	await expect(page.getByTestId("submitted-count")).toHaveText("1/1");
	await expect(page.getByTestId("report-items")).toContainText(`Bài ${stamp}`);

	// logout → owner xem BÁO CÁO LỚP
	await page.getByTestId("logout").click();
	await expect(page).toHaveURL(/\/login/);
	await page.waitForLoadState("networkidle");
	const ou = page.getByLabel("Tên đăng nhập");
	await ou.fill("owner");
	await expect(ou).toHaveValue("owner");
	await page.getByLabel("Mật khẩu").fill("owner123");
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/dashboard/);

	await page.goto("/bao-cao");
	await page.getByTestId("class-select").selectOption({ label: `Lớp ${stamp}` });
	await expect(page.getByTestId("class-avg")).toHaveText("100");
	await expect(page.getByTestId("completion-rate")).toHaveText("100%");
	const srow = page
		.getByTestId("student-table")
		.locator("tr")
		.filter({ hasText: `HS ${stamp}` });
	await expect(srow).toContainText("1/1");

	// drill xuống báo cáo học sinh
	await srow.getByRole("link", { name: `HS ${stamp}` }).click();
	await expect(page).toHaveURL(/\/bao-cao\/hoc-sinh\//);
	await expect(page.getByTestId("avg-score")).toHaveText("100");
	await expect(page.getByTestId("report-items")).toContainText(`Bài ${stamp}`);
});
