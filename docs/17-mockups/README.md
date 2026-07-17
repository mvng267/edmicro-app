# Mockups — Màn hình chính theo HeroUI

**Trạng thái:** 🟢 Đã chốt

> Mockup **HTML tĩnh** — mở trực tiếp file `.html` bằng browser, không cần cài đặt gì. Toàn bộ style từ [`_shared/heroui.css`](_shared/heroui.css) — CSS tái tạo design token HeroUI (palette, radius, shadow, light/dark tự theo hệ điều hành).
>
> **Cách dùng chú thích component:** mỗi mockup có checkbox **"Hiện tên component HeroUI"** ở góc phải dưới — bật lên để thấy nhãn tím ghi tên component HeroUI thật cho từng vùng UI (`data-c="..."`). Khi implement, map 1-1 các vùng này sang component HeroUI — đảm bảo cam kết **100% HeroUI**.
>
> Mockup thể hiện **bố cục và luồng**, không phải pixel-perfect design. Dữ liệu trong mockup là dữ liệu ví dụ.

## Danh sách màn hình (24)

| # | Màn hình | File | Vai trò | Khung | SRS liên quan |
|---|---|---|---|---|---|
| 1 | Đăng nhập theo tenant | [auth/dang-nhap.html](auth/dang-nhap.html) | tất cả | Desktop | ORG, AUTH |
| 2 | Dashboard học sinh | [hoc-sinh/dashboard.html](hoc-sinh/dashboard.html) | student | 📱 Mobile | ASSIGN, COURSE, REPORT, GAME |
| 3 | Trang bài học trong khóa | [hoc-sinh/khoa-hoc.html](hoc-sinh/khoa-hoc.html) | student | 📱 Mobile | COURSE |
| 4 | Làm practice Nghe/Đọc | [hoc-sinh/practice-lam-bai.html](hoc-sinh/practice-lam-bai.html) | student | 📱 Mobile | PRACTICE |
| 5 | Làm practice Nói (ghi âm) | [hoc-sinh/practice-speaking.html](hoc-sinh/practice-speaking.html) | student | 📱 Mobile | PRACTICE, GRADE |
| 6 | Làm bài thi (đồng hồ + điều hướng) | [hoc-sinh/exam-lam-bai.html](hoc-sinh/exam-lam-bai.html) | student | Desktop | EXAM |
| 7 | Kết quả + xem lại bài | [hoc-sinh/ket-qua.html](hoc-sinh/ket-qua.html) | student | 📱 Mobile | GRADE, REPORT, GAME |
| 8 | Bảng xếp hạng | [hoc-sinh/bang-xep-hang.html](hoc-sinh/bang-xep-hang.html) | student | 📱 Mobile | GAME |
| 9 | Dashboard giáo viên | [giao-vien/dashboard.html](giao-vien/dashboard.html) | teacher | Desktop | ASSIGN, GRADE, REPORT |
| 10 | Giao bài (wizard 3 bước) | [giao-vien/giao-bai.html](giao-vien/giao-bai.html) | teacher | Desktop | ASSIGN |
| 11 | Hàng đợi chấm bài | [giao-vien/cham-bai-queue.html](giao-vien/cham-bai-queue.html) | teacher, assistant | Desktop | GRADE |
| 12 | Review 1 bài nói (3 cột) | [giao-vien/cham-bai-review.html](giao-vien/cham-bai-review.html) | teacher, assistant | Desktop | GRADE |
| 13 | Báo cáo lớp | [giao-vien/bao-cao-lop.html](giao-vien/bao-cao-lop.html) | teacher | Desktop | REPORT |
| 14 | Điểm danh buổi học | [giao-vien/diem-danh.html](giao-vien/diem-danh.html) | teacher, assistant | Desktop | SCHED, NOTIF |
| 15 | Báo cáo tổng quan trung tâm | [ban-giam-hieu/bao-cao-tong-quan.html](ban-giam-hieu/bao-cao-tong-quan.html) | owner, manager | Desktop | REPORT, PLAN |
| 16 | Ngân hàng câu hỏi | [noi-dung/ngan-hang-cau-hoi.html](noi-dung/ngan-hang-cau-hoi.html) | content_editor, teacher | Desktop | CONTENT |
| 17 | Cổng phụ huynh — kết quả của con | [phu-huynh/dashboard.html](phu-huynh/dashboard.html) | parent | 📱 Mobile | REPORT (5.4), SCHED, ORG |
| 18 | Cài đặt trung tâm (5 tab) | [chu-trung-tam/cai-dat-trung-tam.html](chu-trung-tam/cai-dat-trung-tam.html) | owner | Desktop | ORG, NOTIF, AUTH, PLAN |
| 19 | Quản trị log + diff + usage | [chu-trung-tam/quan-tri-log.html](chu-trung-tam/quan-tri-log.html) | owner | Desktop | LOG |
| 20 | Quản lý tài khoản (+ modal reset) | [it-admin/quan-ly-tai-khoan.html](it-admin/quan-ly-tai-khoan.html) | it_admin | Desktop | ORG, AUTH |
| 21 | Import học sinh Excel (wizard bước 2/3) | [it-admin/import-hoc-sinh.html](it-admin/import-hoc-sinh.html) | it_admin, manager | Desktop | ORG (5.2) |
| 22 | Duyệt nội dung tổ chuyên môn | [to-truong/duyet-noi-dung.html](to-truong/duyet-noi-dung.html) | academic_head | Desktop | CONTENT, AUTH |
| 23 | Quản trị tenant (cổng ops) | [ops/quan-tri-tenant.html](ops/quan-tri-tenant.html) | admin | Desktop | PLAN, ORG |
| 24 | Hàng đợi ticket + impersonation | [ops/ho-tro-ticket.html](ops/ho-tro-ticket.html) | support_agent | Desktop | SUPPORT |

Đã phủ **11/11 vai trò** (mỗi vai trò ≥1 màn đặc thù; manager dùng chung màn giao bài/báo cáo/điểm danh với teacher + màn 15). Màn còn ghi "_sẽ bổ sung_" trong SRS (soạn practice/exam của GV, giám sát phòng thi, timeline log chi tiết…) vẽ ở vòng 3 khi bắt đầu implement từng module.

## Ánh xạ class mockup → component HeroUI

| Class trong mockup | Component HeroUI khi implement |
|---|---|
| `.navbar` | `Navbar`, `NavbarBrand`, `NavbarContent`, `NavbarItem` |
| `.sidebar .item` | `Listbox` / `ListboxItem` (hoặc custom nav dùng `Link`) |
| `.card`, `.card-header/body/footer` | `Card`, `CardHeader`, `CardBody`, `CardFooter` |
| `.btn` (+ `.primary/.flat-*/.bordered/.light`) | `Button` với `color` + `variant` (solid/flat/bordered/light) |
| `.chip` (+ màu) | `Chip` với `color` + `variant` |
| `.avatar` | `Avatar` |
| `.tbl` | `Table`, `TableHeader`, `TableColumn`, `TableBody`, `TableRow`, `TableCell` |
| `.tabs .tab` | `Tabs`, `Tab` |
| `.progress` | `Progress` |
| `.ring` | `CircularProgress` |
| `.input/.select/.textarea` | `Input`, `Select`, `Textarea` (+ `DatePicker`, `Autocomplete` khi cần) |
| `.switch/.check/.radio` | `Switch`, `Checkbox`, `RadioGroup`+`Radio` |
| `.modal*` | `Modal`, `ModalContent`, `ModalHeader/Body/Footer` |
| `.accordion` | `Accordion`, `AccordionItem` |
| `.breadcrumbs` | `Breadcrumbs`, `BreadcrumbItem` |
| `.pagination` | `Pagination` |
| `.alert` | `Alert` |
| `.bottom-tabs` | `Tabs` (placement bottom) hoặc custom bar dùng `Link` — quyết định khi implement |
| badge số trên chuông | `Badge` |
| panel preview trượt | `Drawer` |
| chọn ngày giờ | `DatePicker` / `DateRangePicker` |

## Quy ước khi thêm mockup mới

1. Copy khung từ mockup cùng loại (mobile: `hoc-sinh/dashboard.html`, desktop: `giao-vien/dashboard.html`).
2. Chỉ dùng class có sẵn trong `_shared/heroui.css`; thiếu thì thêm class mới vào CSS chung (đừng viết style riêng lẻ).
3. Mọi vùng UI phải có `data-c="TênComponentHeroUI"`.
4. Cuối trang ghi chú map sang SRS module nào.
5. Cập nhật bảng danh sách màn hình ở file này.

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-16 | Tạo 16 mockup vòng 1 + CSS design token | Claude |
| 2026-07-16 | Chốt — chuyển trạng thái Đã chốt | Chủ sản phẩm |
| 2026-07-17 | Cập nhật vai trò màn BGH (owner/manager) + danh sách mockup vòng 2 (cổng phụ huynh, cài đặt owner) | Chủ sản phẩm + Claude |
| 2026-07-17 | Vòng 2: thêm 8 màn cho 6 vai trò còn thiếu (parent, owner, it_admin, academic_head, admin, support) — 24 màn, phủ 11/11 vai trò | Chủ sản phẩm + Claude |
