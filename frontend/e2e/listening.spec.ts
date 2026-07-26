import { expect, test } from "@playwright/test";

// Nghe: GV upload audio cho câu hỏi → HS làm bài THẤY player (blob qua API có token)
// → xem lại kết quả cũng có player.
test("câu nghe có audio: soạn → làm bài → xem lại", async ({ page }) => {
	const stamp = Date.now().toString().slice(-6);
	// WAV hợp lệ tối thiểu (44 byte header + im lặng)
	const wav = Buffer.concat([
		Buffer.from("RIFF"),
		Buffer.from([36, 0, 0, 0]),
		Buffer.from("WAVEfmt "),
		Buffer.from([16, 0, 0, 0, 1, 0, 1, 0, 0x44, 0xac, 0, 0, 0x88, 0x58, 1, 0, 2, 0, 16, 0]),
		Buffer.from("data"),
		Buffer.from([0, 0, 0, 0]),
	]);

	// owner login + dựng lớp/HS
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

	// câu NGHE: đính audio + publish
	await page.goto("/content");
	await page.getByTestId("q-type").selectOption("mcq_single");
	await page.getByTestId("q-skill").selectOption("listening");
	await page.getByTestId("q-prompt").fill(`Nghe ${stamp} và chọn:`);
	await page.getByTestId("q-option-0").fill("cat");
	await page.getByTestId("q-option-1").fill("cut");
	await page.getByTestId("q-correct-0").check();
	await page
		.getByTestId("q-audio")
		.setInputFiles({ name: "listen.wav", mimeType: "audio/wav", buffer: wav });
	await page.getByTestId("q-publish").click();
	await expect(page.getByTestId("q-list")).toContainText(`Nghe ${stamp}`);

	// practice + giao
	await page.goto("/practices");
	await page.getByTestId("practice-name").fill(`Bài nghe ${stamp}`);
	await page
		.getByTestId("pick-list")
		.locator("li")
		.filter({ hasText: `Nghe ${stamp}` })
		.locator("input[type=checkbox]")
		.check();
	await page.getByTestId("save-practice").click();
	const row = page
		.getByTestId("practice-list")
		.locator("li")
		.filter({ hasText: `Bài nghe ${stamp}` })
		.first();
	await expect(row).toBeVisible();
	await page.getByTestId("assign-class").selectOption({ label: `Lớp ${stamp}` });
	await row.getByRole("button", { name: "Giao cho lớp" }).click();
	await expect(page.getByText(/Đã giao cho \d+ học sinh/)).toBeVisible();

	// HS login (đổi mật khẩu lần đầu) → làm bài
	await page.getByTestId("logout").click();
	await expect(page).toHaveURL(/\/login/);
	await page.waitForLoadState("networkidle");
	const u = page.getByLabel("Tên đăng nhập");
	await u.fill(username);
	await expect(u).toHaveValue(username);
	await page.getByLabel("Mật khẩu").fill(password);
	await page.getByRole("button", { name: "Đăng nhập" }).click();
	await expect(page).toHaveURL(/\/doi-mat-khau/);
	await page.getByLabel("Mật khẩu hiện tại").fill(password);
	await page.getByLabel("Mật khẩu mới", { exact: true }).fill("MatKhauMoi123");
	await page.getByLabel("Nhập lại mật khẩu mới").fill("MatKhauMoi123");
	await page.getByRole("button", { name: "Đổi mật khẩu và vào học" }).click();
	await expect(page).toHaveURL(/\/dashboard/);

	await page.goto("/hoc");
	await page
		.getByTestId("todo-list")
		.getByRole("button", { name: "Làm bài" })
		.click();
	await expect(page).toHaveURL(/\/hoc\/lam-bai\//);

	// PLAYER hiển thị + có blob src (tải audio qua API thành công)
	const player = page.getByTestId("audio-player");
	await expect(player).toBeVisible();
	await expect(player).toHaveAttribute("src", /^blob:/);

	// làm + nộp → xem lại cũng có player
	await page.getByTestId("ans-0-0").check();
	await expect(page.getByTestId("saved")).toBeVisible();
	await page.getByTestId("submit-attempt").click();
	await expect(page).toHaveURL(/\/hoc\/ket-qua\//);
	await expect(page.getByTestId("score")).toHaveText("100");
	await expect(page.getByTestId("audio-player")).toBeVisible();
});
