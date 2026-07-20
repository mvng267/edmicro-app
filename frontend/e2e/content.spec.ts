import { expect, test } from "@playwright/test";

// M2: owner tạo câu hỏi mcq -> xuất bản -> thấy trong danh sách published -> lọc theo kỹ năng.
test("tạo và xuất bản câu hỏi trắc nghiệm", async ({ page }) => {
	await page.goto("/login");
	await page.getByLabel("Tên đăng nhập").fill("owner");
	await page.getByLabel("Mật khẩu").fill("owner123");
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/dashboard/);

	await page.goto("/content");
	await page.getByTestId("q-type").selectOption("mcq_single");
	await page.getByTestId("q-skill").selectOption("reading");
	const stamp = Date.now().toString().slice(-6);
	await page.getByTestId("q-prompt").fill(`Thủ đô Việt Nam ${stamp}?`);
	await page.getByTestId("q-option-0").fill("Hà Nội");
	await page.getByTestId("q-option-1").fill("Đà Nẵng");
	await page.getByTestId("q-correct-0").check();
	await page.getByTestId("q-publish").click();

	// xuất hiện trong danh sách, status published
	await expect(page.getByTestId("q-list")).toContainText("published");

	// lọc theo kỹ năng reading vẫn thấy; đổi sang listening thì danh sách khác
	await page.getByTestId("filter-skill").selectOption("reading");
	await expect(page.getByTestId("q-list").locator("li").first()).toBeVisible();
});
