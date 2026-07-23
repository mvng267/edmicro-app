import { expect, test } from "@playwright/test";

// M9: GV tạo khóa học + bài + giao lớp → HS hoàn thành bài → tiến độ + điểm tăng.
test("khóa học: hoàn thành bài → tiến độ + điểm", async ({ page }) => {
	const stamp = Date.now().toString().slice(-6);

	// owner login + dựng lớp + HS
	await page.goto("/login");
	await page.getByLabel("Tên đăng nhập").fill("owner");
	await page.getByLabel("Mật khẩu").fill("owner123");
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/dashboard/);

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

	// tạo khóa học + bài + giao lớp
	await page.goto("/khoa-hoc");
	await page.getByTestId("course-name").fill(`Khóa ${stamp}`);
	await page.getByTestId("add-course").click();
	const crow = page
		.getByTestId("course-list")
		.locator("li")
		.filter({ hasText: `Khóa ${stamp}` });
	await expect(crow).toBeVisible();
	await crow.getByRole("button", { name: "Quản lý" }).click();
	await page.getByTestId("lesson-title").fill(`Bài ${stamp}`);
	await page.getByTestId("add-lesson").click();
	await expect(page.getByTestId("assign-class")).toBeVisible();
	await page.getByTestId("assign-class").selectOption({ label: `Lớp ${stamp}` });
	await page.getByTestId("assign-course").click();
	await expect(page.getByText("Đã giao khóa cho lớp")).toBeVisible();

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

	// HS: khóa học của tôi → điểm 0, tiến độ 0 → hoàn thành bài
	await page.goto("/hoc/khoa-hoc");
	await expect(page.getByTestId("my-points")).toContainText("0 điểm");
	const mine = page
		.getByTestId("my-course-list")
		.locator("li")
		.filter({ hasText: `Khóa ${stamp}` });
	await expect(mine).toContainText("0/1 bài");
	await mine.getByRole("button", { name: "Học" }).click();
	await page.getByRole("button", { name: "Hoàn thành" }).click();

	// tiến độ 100% + điểm +5 (hoàn thành bài chưa cấp badge — cần nộp bài/100đ/streak)
	await expect(mine).toContainText("1/1 bài · 100%");
	await expect(page.getByTestId("my-points")).toContainText("5 điểm");
	await expect(page.getByTestId("my-streak")).toContainText("chuỗi 1 ngày");
});
