import { expect, test } from "@playwright/test";

// M7: GV tạo ĐỀ THI (có thời lượng) → giao → HS thi thấy ĐỒNG HỒ server → nộp → kết quả có BAND.
test("đề thi: đồng hồ server + quy đổi band", async ({ page }) => {
	const stamp = Date.now().toString().slice(-6);

	// owner login
	await page.goto("/login");
	await page.getByLabel("Tên đăng nhập").fill("owner");
	await page.getByLabel("Mật khẩu").fill("owner123");
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/dashboard/);

	// chi nhánh + lớp + HS
	await page.goto("/org/branches");
	await page.getByTestId("branch-name").fill(`CN ${stamp}`);
	await page.getByTestId("add-branch").click();
	await expect(page.getByTestId("branch-list")).toContainText(`CN ${stamp}`);

	await page.goto("/org/classes");
	await page.getByTestId("branch-select").selectOption({ label: `CN ${stamp}` });
	await page.getByTestId("class-name").fill(`Lớp ${stamp}`);
	await page.getByTestId("add-class").click();
	await expect(page.getByTestId("class-list")).toContainText(`Lớp ${stamp}`);

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

	// 2 câu mcq (đáp án đúng = A) publish
	await page.goto("/content");
	for (const suffix of ["một", "hai"]) {
		await page.getByTestId("q-type").selectOption("mcq_single");
		await page.getByTestId("q-prompt").fill(`EQ ${stamp} ${suffix}`);
		await page.getByTestId("q-option-0").fill("Đúng");
		await page.getByTestId("q-option-1").fill("Sai");
		await page.getByTestId("q-correct-0").check();
		await page.getByTestId("q-publish").click();
		await expect(page.getByTestId("q-list")).toContainText(`EQ ${stamp} ${suffix}`);
	}

	// tạo ĐỀ THI 1 phút gồm 2 câu + giao lớp
	await page.goto("/exams");
	await page.getByTestId("exam-name").fill(`Đề ${stamp}`);
	await page.getByTestId("exam-duration").fill("1");
	for (const suffix of ["một", "hai"]) {
		await page
			.getByTestId("pick-list")
			.locator("li")
			.filter({ hasText: `EQ ${stamp} ${suffix}` })
			.locator("input[type=checkbox]")
			.check();
	}
	await page.getByTestId("save-exam").click();
	const erow = page
		.getByTestId("exam-list")
		.locator("li")
		.filter({ hasText: `Đề ${stamp}` })
		.first();
	await expect(erow).toBeVisible();
	await page.getByTestId("assign-class").selectOption({ label: `Lớp ${stamp}` });
	await erow.getByRole("button", { name: "Giao cho lớp" }).click();
	await expect(page.getByText(/Đã giao cho \d+ học sinh/)).toBeVisible();

	// logout → HS login → thi
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

	// ĐỒNG HỒ server hiển thị đếm ngược
	await expect(page.getByTestId("exam-timer")).toBeVisible();

	// trả lời 2 câu đúng (option A) → nộp
	await page.getByTestId("ans-0-0").check();
	await page.getByTestId("ans-1-0").check();
	await expect(page.getByTestId("saved")).toBeVisible();
	await page.getByTestId("submit-attempt").click();

	// kết quả: điểm 100 + BAND quy đổi (100% → "8.0+")
	await expect(page).toHaveURL(/\/hoc\/ket-qua\//);
	await expect(page.getByTestId("score")).toHaveText("100");
	await expect(page.getByTestId("band")).toContainText("8.0+");
});
