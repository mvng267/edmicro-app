import { expect, test } from "@playwright/test";

test("owner đăng nhập thành công và thấy dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Tên đăng nhập").fill("owner");
  await page.getByLabel("Mật khẩu").fill("owner123");
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByTestId("greeting")).toBeVisible();
  await expect(page.getByTestId("role")).toHaveText("owner");
});

test("sai mật khẩu hiện thông báo lỗi", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Tên đăng nhập").fill("owner");
  await page.getByLabel("Mật khẩu").fill("saimatkhau");
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page.getByText("Sai tên đăng nhập hoặc mật khẩu")).toBeVisible();
});
