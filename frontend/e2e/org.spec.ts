import { expect, test } from "@playwright/test";

// Luồng M1: owner dựng bộ máy (chi nhánh -> lớp -> tài khoản HS) rồi HS đăng nhập được.
test("owner dựng bộ máy rồi học sinh mới đăng nhập được", async ({ page }) => {
	// 1. owner login
	await page.goto("/login");
	await page.getByLabel("Tên đăng nhập").fill("owner");
	await page.getByLabel("Mật khẩu").fill("owner123");
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/dashboard/);

	// 2. tạo chi nhánh
	const stamp = Date.now().toString().slice(-6);
	await page.goto("/org/branches");
	await page.getByTestId("branch-name").fill(`CN ${stamp}`);
	await page.getByTestId("add-branch").click();
	await expect(page.getByTestId("branch-list")).toContainText(`CN ${stamp}`);

	// 3. tạo lớp (chọn chi nhánh vừa tạo)
	await page.goto("/org/classes");
	await page
		.getByTestId("branch-select")
		.selectOption({ label: `CN ${stamp}` });
	await page.getByTestId("class-name").fill(`IELTS ${stamp}`);
	await page.getByTestId("add-class").click();
	await expect(page.getByTestId("class-list")).toContainText(`IELTS ${stamp}`);

	// 4. tạo học sinh, lấy username + password
	await page.goto("/org/users");
	await page.getByTestId("user-name").fill(`Học Sinh ${stamp}`);
	await page.getByTestId("role-select").selectOption("student");
	await page.getByTestId("add-user").click();
	await expect(page.getByTestId("cred-box")).toBeVisible();
	const username =
		(await page.getByTestId("cred-username").textContent())?.trim() ?? "";
	const password =
		(await page.getByTestId("cred-password").textContent())?.trim() ?? "";
	expect(username).not.toEqual("");
	expect(password).not.toEqual("");

	// 5. logout
	await page.getByTestId("logout").click();
	await expect(page).toHaveURL(/\/login/);
	await page.waitForLoadState("networkidle");

	// 6. học sinh mới đăng nhập (fill + verify value để tránh race hydration)
	const userInput = page.getByLabel("Tên đăng nhập");
	const pwInput = page.getByLabel("Mật khẩu");
	await expect(userInput).toBeVisible();
	await userInput.fill(username);
	await expect(userInput).toHaveValue(username);
	await pwInput.fill(password);
	await expect(pwInput).toHaveValue(password);
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/dashboard/);
	await expect(page.getByTestId("role")).toHaveText("student");
});
