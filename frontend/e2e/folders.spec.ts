import { expect, test } from "@playwright/test";

// Kho câu hỏi: cây thư mục (tạo/đổi tên) → soạn câu vào thư mục → lọc → SỬA câu (version mới).
test("kho câu hỏi: thư mục + sửa câu hỏi", async ({ page }) => {
	const stamp = Date.now().toString().slice(-6);

	await page.goto("/login");
	await page.getByLabel("Tên đăng nhập").fill("owner");
	await page.getByLabel("Mật khẩu").fill("owner123");
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/dashboard/);

	await page.goto("/content");

	// tạo thư mục gốc (prompt dialog)
	page.once("dialog", (d) => d.accept(`Kho ${stamp}`));
	await page.getByTestId("folder-add-root").click();
	const folderBtn = page
		.locator("aside ~ * , div")
		.getByText(`Kho ${stamp}`)
		.first();
	await expect(folderBtn).toBeVisible();

	// chọn thư mục → soạn câu vào đó
	await folderBtn.click();
	await page.getByTestId("toggle-form").click();
	await page.getByTestId("q-prompt").fill(`Trong kho ${stamp}?`);
	await page.getByTestId("q-option-0").fill("A");
	await page.getByTestId("q-option-1").fill("B");
	await page.getByTestId("q-correct-0").check();
	await page.getByTestId("q-publish").click();
	await expect(page.getByTestId("q-list")).toContainText(`Trong kho ${stamp}?`);

	// lọc "Chưa phân loại" KHÔNG thấy câu này; quay lại thư mục thì thấy
	await page.getByTestId("folder-none").click();
	await expect(page.getByTestId("q-list")).not.toContainText(
		`Trong kho ${stamp}?`,
	);
	await page.getByText(`Kho ${stamp}`).first().click();
	await expect(page.getByTestId("q-list")).toContainText(`Trong kho ${stamp}?`);

	// SỬA câu → đổi đề bài → lưu phiên bản mới
	const row = page
		.getByTestId("q-list")
		.locator("li")
		.filter({ hasText: `Trong kho ${stamp}?` });
	await row.getByRole("button", { name: "Sửa" }).click();
	await expect(
		page.getByText("Đang sửa câu hỏi", { exact: false }),
	).toBeVisible();
	await page.getByTestId("q-prompt").fill(`Đã sửa ${stamp}?`);
	await page.getByTestId("q-save-draft").click();
	await expect(page.getByTestId("q-list")).toContainText(`Đã sửa ${stamp}?`);
});
