import { expect, test } from "@playwright/test";

// M10: ticket hỗ trợ (tạo → comment → đóng) + trang quản trị log + mức dùng.
test("hỗ trợ: ticket + quản trị log + mức dùng", async ({ page }) => {
	const stamp = Date.now().toString().slice(-6);

	await page.goto("/login");
	await page.getByLabel("Tên đăng nhập").fill("owner");
	await page.getByLabel("Mật khẩu").fill("owner123");
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/dashboard/);

	// tạo ticket
	await page.goto("/ho-tro");
	await page.getByTestId("ticket-subject").fill(`Ticket ${stamp}`);
	await page.getByTestId("ticket-body").fill("Mô tả lỗi");
	await page.getByTestId("create-ticket").click();
	const row = page
		.getByTestId("ticket-list")
		.locator("li")
		.filter({ hasText: `Ticket ${stamp}` });
	await expect(row).toBeVisible();

	// mở → comment → đóng
	await row.getByRole("button", { name: "Mở" }).click();
	await page.getByTestId("comment-body").fill("Đang xử lý");
	await page.getByTestId("send-comment").click();
	await expect(page.getByTestId("comments")).toContainText("Đang xử lý");
	await page.getByTestId("close-ticket").click();
	await expect(row).toContainText("closed");

	// quản trị mức dùng
	await page.goto("/quan-tri/usage");
	await expect(page.getByTestId("usage")).toBeVisible();

	// quản trị log
	await page.goto("/quan-tri/log");
	await expect(page.getByTestId("log-table")).toBeVisible();
});
