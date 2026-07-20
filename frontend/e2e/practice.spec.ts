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
	await page
		.getByTestId("pick-list")
		.locator("input[type=checkbox]")
		.first()
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

	// chọn đáp án → thấy "Đã lưu" (autosave) → nộp
	await page.getByTestId("ans-0-0").check();
	await expect(page.getByTestId("saved")).toBeVisible();
	await page.getByTestId("submit-attempt").click();

	// quay lại việc cần làm, trạng thái submitted
	await expect(page).toHaveURL(/\/hoc$/);
	await expect(page.getByTestId("todo-list")).toContainText("submitted");
});
