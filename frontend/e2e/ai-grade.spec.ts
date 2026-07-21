import { expect, test } from "@playwright/test";

// M6: giao bài WRITING → HS làm → AI chấm sơ bộ (chờ GV) → GV chốt điểm.
test("bài writing: AI chấm sơ bộ rồi giáo viên chốt điểm", async ({ page }) => {
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
	await page.getByTestId("branch-select").selectOption({ label: `CN ${stamp}` });
	await page.getByTestId("class-name").fill(`Lớp ${stamp}`);
	await page.getByTestId("add-class").click();
	await expect(page.getByTestId("class-list")).toContainText(`Lớp ${stamp}`);

	// học sinh trong lớp
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

	// câu WRITING publish
	await page.goto("/content");
	await page.getByTestId("q-type").selectOption("writing");
	await page.getByTestId("q-prompt").fill(`Viết ${stamp} về thành phố của bạn`);
	await page.getByTestId("q-rubric").fill("IELTS Writing Task 2");
	await page.getByTestId("q-publish").click();
	await expect(page.getByTestId("q-list")).toContainText("published");

	// practice chỉ 1 câu writing + giao lớp
	await page.goto("/practices");
	await page.getByTestId("practice-name").fill(`Bài viết ${stamp}`);
	await page
		.getByTestId("pick-list")
		.locator("li")
		.filter({ hasText: `Viết ${stamp}` })
		.locator("input[type=checkbox]")
		.check();
	await page.getByTestId("save-practice").click();
	const row = page
		.getByTestId("practice-list")
		.locator("li")
		.filter({ hasText: `Bài viết ${stamp}` })
		.first();
	await expect(row).toBeVisible();
	await page.getByTestId("assign-class").selectOption({ label: `Lớp ${stamp}` });
	await row.getByRole("button", { name: "Giao cho lớp" }).click();
	await expect(page.getByText(/Đã giao cho \d+ học sinh/)).toBeVisible();

	// logout → HS login → làm bài viết
	await page.getByTestId("logout").click();
	await expect(page).toHaveURL(/\/login/);
	await page.waitForLoadState("networkidle");
	const u = page.getByLabel("Tên đăng nhập");
	await u.fill(username);
	await expect(u).toHaveValue(username);
	await page.getByLabel("Mật khẩu").fill(password);
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/dashboard/);

	await page.goto("/hoc");
	await page
		.getByTestId("todo-list")
		.getByRole("button", { name: "Làm bài" })
		.click();
	await expect(page).toHaveURL(/\/hoc\/lam-bai\//);

	// viết bài (autosave) → nộp
	await page
		.getByTestId("write-0")
		.fill(
			"My city is a lively place full of energy where many people work and study " +
				"across different neighborhoods every single day with great enthusiasm.",
		);
	await expect(page.getByTestId("saved")).toBeVisible();
	await page.getByTestId("submit-attempt").click();

	// kết quả: điểm tạm tính + câu tự luận chờ GV duyệt
	await expect(page).toHaveURL(/\/hoc\/ket-qua\//);
	await expect(page.getByTestId("provisional-banner")).toBeVisible();
	await expect(page.getByTestId("verdict-0")).toContainText("Chờ GV duyệt");

	// về việc cần làm (có AppShell) → logout → owner vào HÀNG ĐỢI CHẤM
	await page.getByTestId("back-hoc").click();
	await expect(page).toHaveURL(/\/hoc$/);
	await page.getByTestId("logout").click();
	await expect(page).toHaveURL(/\/login/);
	await page.waitForLoadState("networkidle");
	const ou = page.getByLabel("Tên đăng nhập");
	await ou.fill("owner");
	await expect(ou).toHaveValue("owner");
	await page.getByLabel("Mật khẩu").fill("owner123");
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/dashboard/);

	await page.goto("/cham-bai");
	const qrow = page
		.getByTestId("grading-queue")
		.locator("li")
		.filter({ hasText: `HS ${stamp}` });
	await expect(qrow).toBeVisible();
	await qrow.click();
	await expect(page).toHaveURL(/\/cham-bai\//);

	// AI đã đề xuất điểm; GV chốt 1.0
	await expect(page.getByTestId("review-card-0")).toContainText("AI đề xuất");
	await page.getByTestId("final-score-0").fill("1");
	await page.getByTestId("final-feedback-0").fill("Bài tốt, ý rõ ràng.");
	await page.getByTestId("finalize-0").click();
	await expect(page.getByTestId("review-card-0")).toContainText("Đã chốt");
});
