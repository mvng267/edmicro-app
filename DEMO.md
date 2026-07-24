# Tài khoản & dữ liệu DEMO — Edmicro App

> Cập nhật: 2026-07-21 · Môi trường demo: **https://b2b.dalianperfume.com** (tenant `b2b`)

Tenant được nhận diện qua **subdomain**: `b2b.dalianperfume.com` → slug `b2b`. Vào domain là ra thẳng màn đăng nhập.

---

## 1. Tài khoản đăng nhập

Tất cả dùng chung tenant `b2b`. Mật khẩu để đơn giản cho demo — **đổi trước khi dùng thật**.

| Tài khoản | Mật khẩu | Vai trò | Vào để xem gì |
|---|---|---|---|
| `owner` | `owner123` | Chủ trung tâm | Toàn quyền: mọi lớp, báo cáo, chấm bài, log, mức dùng |
| `manager` | `manager123` | NV quản lý học vụ | Vận hành: lớp, tài khoản, báo cáo, lịch học, mức dùng |
| `head` | `head123` | Tổ trưởng chuyên môn | Duyệt nội dung + báo cáo theo tổ |
| `itadmin` | `it123` | IT trung tâm | Tài khoản, phân lớp, quản trị log — **không** thấy dữ liệu học tập |
| `teacher` | `teacher123` | Giáo viên | Giao bài, **chấm bài viết**, báo cáo lớp mình, điểm danh |
| `assistant` | `assist123` | Trợ giảng | Xem lớp được gán, điểm danh (chỉ đọc báo cáo) |
| `content` | `content123` | NV nội dung | Ngân hàng câu hỏi, soạn/xuất bản câu hỏi |
| `support` | `support123` | NV hỗ trợ | Ticket hỗ trợ; đăng nhập thay (impersonation, có ghi audit) |
| `hs1` | `hs123` | Học sinh — **Học Sinh An** | Đã học nhiều nhất: 35 điểm, huy hiệu, khóa học 50% |
| `hs2` | `hs123` | Học sinh — **Học Sinh Bình** | Nộp bài sai một phần, đi học muộn |
| `hs3` | `hs123` | Học sinh — **Học Sinh Chi** | **Chưa nộp bài**, bị điểm danh vắng, có 3 thông báo |
| `parent` | `parent123` | Phụ huynh | Cổng phụ huynh — xem báo cáo + điểm của **Học Sinh An** |

---

## 2. Dữ liệu demo đã có sẵn

**Tổ chức**
- Chi nhánh: **CN Demo Cầu Giấy** (144 Xuân Thủy, Hà Nội)
- Lớp: **IELTS 6.0 — Lớp A** (hs1, hs2, hs3) · **TOEIC Cơ bản — Lớp B** (hs3)
- `teacher` + `assistant` được gán dạy **cả 2 lớp**; `parent` liên kết với `hs1`

**Nội dung** — 6 câu hỏi đã xuất bản: 4 trắc nghiệm (3 reading + 1 listening), 1 điền từ, 1 **writing** (có rubric IELTS)

**Đã giao cho lớp IELTS**
| Loại | Tên | Ghi chú |
|---|---|---|
| Practice | Luyện tập Unit 1 — Từ vựng & Ngữ pháp | 4 câu, **hạn sau 20 giờ** (để test nhắc deadline) |
| Practice (viết) | Bài viết — Hometown | 1 câu writing → AI chấm sơ bộ → GV chốt |
| Đề thi | Thi thử giữa khóa | **30 phút**, có đồng hồ server + quy đổi band |
| Khóa học | Khóa IELTS Foundation | 4 bài: text · video · flashcard · **practice nhúng** |

**Trạng thái học tập đã mô phỏng**
- **hs1**: nộp practice đúng hết → **35 điểm**, huy hiệu *Khởi động*, hoàn thành 2/4 bài học (**50%**); đã nộp bài viết → **đang chờ GV chốt điểm**
- **hs2**: nộp practice sai một phần → 10 điểm
- **hs3**: **chưa nộp gì** (để test báo cáo "chưa nộp" + nhắc deadline)

**Lịch học & điểm danh** — 2 buổi (1 buổi đã qua đã điểm danh, 1 buổi ngày mai có link online)
- hs1 có mặt · hs2 **muộn** · hs3 **vắng** → hs3 nhận thông báo vắng mặt

**Khác** — thông báo giao bài + nhắc deadline đã phát; 1 **ticket hỗ trợ đang mở** ("Không xuất được báo cáo lớp")

---

## 3. Kịch bản test nhanh theo vai trò

### Giáo viên (`teacher` / `teacher123`)
1. **Chấm bài (GV)** → thấy 1 bài của *Học Sinh An* chờ chấm → mở → xem bài viết + **điểm AI đề xuất** → sửa điểm + nhận xét → **Chốt điểm**
2. **Báo cáo lớp** → chọn *IELTS 6.0 — Lớp A* → điểm TB lớp, tỉ lệ hoàn thành, ai chưa nộp → bấm tên HS để drill xuống
3. **Lịch học** → chọn lớp → buổi đã qua đã có điểm danh; tạo buổi mới → điểm danh (mặc định "có mặt", chỉnh lệch)
4. **Bài luyện tập / Đề thi / Khóa học** → tạo mới + giao cho lớp

### Học sinh (`hs1` / `hs123`)
1. **Việc cần làm** → làm **Thi thử giữa khóa** → thấy **đồng hồ đếm ngược**, hết giờ tự nộp → kết quả có **Band**
2. **Khóa học của tôi** → 35 điểm, streak, huy hiệu → mở khóa → hoàn thành bài còn lại (mỗi bài +5 điểm)
3. **Báo cáo của tôi** → điểm TB + danh sách bài đã nộp (bấm để xem lại đáp án)
4. 🔔 **chuông** → thông báo bài mới / nhắc deadline

> Đăng nhập `hs3` để thấy góc nhìn HS **chưa làm gì**: 3 thông báo (giao bài, vắng mặt, nhắc deadline).

### Phụ huynh (`parent` / `parent123`)
**Cổng phụ huynh** → chọn con (*Học Sinh An*) → điểm + huy hiệu + báo cáo học tập của con.

### Chủ trung tâm (`owner` / `owner123`)
1. **Bảng xếp hạng** → lớp IELTS: An 35đ · Bình 10đ · Chi 0đ
2. **Mức dùng** → 3 HS · 2 lớp · 3 lượt nộp · 1 khóa + **quota AI writing 1/100**
3. **Quản trị log** → nhật ký thao tác, lọc theo module (ORG/CONTENT/ASSIGN/GRADE…)
4. **Hỗ trợ** → ticket đang mở → trả lời + đóng

### NV hỗ trợ (`support` / `support123`)
Xem **mọi ticket** của trung tâm; có quyền **đăng nhập thay** người dùng (`POST /api/v1/support/impersonate/{user_id}`) — mọi lần đều **ghi audit log**.

---

## 4. Tạo lại / mở rộng dữ liệu

```bash
# Tạo tenant mới (slug phải khớp subdomain sẽ truy cập)
cd backend && PYTHONPATH=. uv run python ../scripts/seed.py <slug> "Tên trung tâm" [mật khẩu owner]

# Seed dữ liệu demo đầy đủ cho tenant đó
cd backend && PYTHONPATH=. uv run python ../scripts/seed_demo.py <slug>
#   chạy lần 2 sẽ báo "đã có dữ liệu demo"; thêm --force nếu muốn seed chồng
```

Script dùng thẳng service layer nên mọi hiệu ứng phụ chạy thật: chấm tự động, AI chấm writing, hàng đợi review, thông báo, điểm/streak/huy hiệu, tiến độ khóa học.

---

## 5. Lưu ý

- **Điểm TB của hs1 là 50** vì bài viết chưa được GV chốt → câu đó tạm tính 0 và bài ở trạng thái *provisional*. Chốt điểm ở màn **Chấm bài** xong điểm sẽ tự tính lại.
- **AI chấm writing** đang dùng `FakeGrader` (tất định, không gọi mạng). Muốn dùng Claude thật: set `ANTHROPIC_API_KEY` trong `backend/.env` rồi restart backend.
- Site đang **public, không giới hạn IP**. Nếu chỉ demo nội bộ nên bật Cloudflare Access.
- Backend (`:8010`), frontend (`:3005`) và cloudflared đang chạy dạng tiến trình nền — **tắt máy là mất**. Cần chạy lâu dài thì dựng systemd/docker-compose.
- Mật khẩu demo rất yếu — **không dùng cho dữ liệu thật**.
