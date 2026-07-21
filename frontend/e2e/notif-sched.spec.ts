import { expect, test } from "@playwright/test";

// M8: giao bài → assignment_created; điểm danh vắng → attendance_absent. HS thấy chuông + 2 thông báo.
test("thông báo giao bài + điểm danh vắng đến học sinh", async ({ page }) => {
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

	// câu hỏi + practice + giao (→ assignment_created)
	await page.goto("/content");
	await page.getByTestId("q-type").selectOption("mcq_single");
	await page.getByTestId("q-prompt").fill(`NS ${stamp}?`);
	await page.getByTestId("q-option-0").fill("A");
	await page.getByTestId("q-option-1").fill("B");
	await page.getByTestId("q-correct-0").check();
	await page.getByTestId("q-publish").click();
	await expect(page.getByTestId("q-list")).toContainText(`NS ${stamp}?`);

	await page.goto("/practices");
	await page.getByTestId("practice-name").fill(`Bài ${stamp}`);
	await page
		.getByTestId("pick-list")
		.locator("li")
		.filter({ hasText: `NS ${stamp}?` })
		.locator("input[type=checkbox]")
		.check();
	await page.getByTestId("save-practice").click();
	const row = page
		.getByTestId("practice-list")
		.locator("li")
		.filter({ hasText: `Bài ${stamp}` })
		.first();
	await expect(row).toBeVisible();
	await page.getByTestId("assign-class").selectOption({ label: `Lớp ${stamp}` });
	await row.getByRole("button", { name: "Giao cho lớp" }).click();
	await expect(page.getByText(/Đã giao cho \d+ học sinh/)).toBeVisible();

	// LỊCH HỌC: tạo buổi + điểm danh HS VẮNG (→ attendance_absent)
	await page.goto("/lich-hoc");
	await page.getByTestId("class-select").selectOption({ label: `Lớp ${stamp}` });
	await page.getByTestId("session-start").fill("2026-08-01T18:00");
	await page.getByTestId("session-end").fill("2026-08-01T20:00");
	await page.getByTestId("session-topic").fill(`Buổi ${stamp}`);
	await page.getByTestId("add-session").click();
	await expect(page.getByTestId("session-list")).toContainText(`Buổi ${stamp}`);
	await page.getByRole("button", { name: "Điểm danh" }).first().click();
	await page.locator('select[data-testid^="att-"]').first().selectOption("absent");
	await page.getByTestId("save-attendance").click();
	await expect(page.getByText(/Đã điểm danh/)).toBeVisible();

	// logout → HS login → chuông có badge + 2 thông báo
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
	await expect(page.getByTestId("notif-badge")).toBeVisible();

	await page.getByTestId("notif-bell").click();
	await expect(page).toHaveURL(/\/thong-bao/);
	await expect(page.getByTestId("notif-list")).toContainText("Bài mới được giao");
	await expect(page.getByTestId("notif-list")).toContainText("Điểm danh: vắng mặt");
});
