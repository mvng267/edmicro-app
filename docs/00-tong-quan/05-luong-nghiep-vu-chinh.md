# Luồng nghiệp vụ chính — truy vết yêu cầu gốc

**Trạng thái:** 🟢 Đã chốt

> Tài liệu này chứng minh bộ SRS phủ **đúng luồng yêu cầu gốc** của chủ sản phẩm, nối các module thành 4 luồng xuyên suốt. Mỗi bước ghi rõ module + FR chịu trách nhiệm — khi đổi yêu cầu, sửa từ đây lần ra các SRS liên quan.

## 1. Bảng truy vết yêu cầu gốc → nơi đáp ứng

| Yêu cầu gốc (nguyên văn chủ sản phẩm) | Nơi đáp ứng |
|---|---|
| "Giảng viên có thể giao bài cho học sinh" | [ASSIGN](../07-giao-bai/srs-giao-bai.md) — FR-ASSIGN-01→20 |
| "Khóa học… trong khóa học có practice, exam, video, flashcard, word excel powerpoint" | [COURSE](../04-khoa-hoc/srs-khoa-hoc.md) — content block 6 loại, FR-COURSE-01→22 |
| "Practice có các bài nghe nói đọc viết" | [PRACTICE](../05-practice/srs-practice.md) + [catalog ~24 loại câu hỏi](../99-phu-luc/01-loai-cau-hoi.md) |
| "Exam là các bài thi thử" | [EXAM](../06-exam/srs-exam.md) — template IELTS/TOEIC/VSTEP/Cambridge/HSK/JLPT/TOPIK |
| "Hệ thống báo cáo đầy đủ học sinh làm bài như nào" | [REPORT](../09-bao-cao/srs-bao-cao.md) — 4 cấp + cổng phụ huynh |
| "Có các quyền: BGH, giáo viên/giảng viên, trợ giảng, học sinh; admin, nhân viên nội dung, support" + "thêm quyền IT trung tâm" + "tách quyền NV quản lý với quyền trung tâm" | [AUTH](../02-phan-quyen/srs-phan-quyen.md) — 11 vai trò, ma trận §6 |
| "B2B phục vụ trung tâm ngoại ngữ" | [Multi-tenant](../01-kien-truc/02-multi-tenant.md), [PLAN](../14-goi-dich-vu/srs-goi-dich-vu.md) |
| "Python, React HeroUI 100%, Postgres, MinIO → S3/R2" | [Kiến trúc](../01-kien-truc/01-kien-truc-tong-the.md), [Lưu trữ file](../01-kien-truc/04-luu-tru-file.md), [Cấu trúc code](../01-kien-truc/05-cau-truc-code.md) |
| "Bảo mật dữ liệu tuyệt đối" | [Bảo mật](../01-kien-truc/03-bao-mat.md) |
| "Quản lý file, code theo module dễ làm dễ sửa; folder doc theo module" | [Cấu trúc code](../01-kien-truc/05-cau-truc-code.md) + cấu trúc `docs/` này |
| "Mọi phần đều log phiên bản — ai sửa gì; có phần quản trị log theo từng phần" | [LOG](../18-quan-tri-log/srs-quan-tri-log.md) — activity log 2 tầng + UI quản trị |

## 2. Luồng A — Onboard trung tâm mới → sẵn sàng dạy

```mermaid
flowchart LR
  A1[admin tao tenant + goi<br/>FR-ORG-01, PLAN] --> A2[owner cau hinh trung tam + kenh Zalo<br/>FR-ORG-03, FR-NOTIF-04]
  A2 --> A3[owner tao manager, it_admin, academic_head + gan pham vi<br/>FR-ORG-08, FR-ORG-23]
  A3 --> A4[owner tao chi nhanh; manager/it_admin tao lop + gan GV TA<br/>FR-ORG-04, FR-ORG-05]
  A4 --> A5[it_admin import hoc sinh Excel + cap tai khoan + consent<br/>FR-ORG-09..11, FR-ORG-17]
  A5 --> A6[it_admin tao tai khoan phu huynh + lien ket con<br/>FR-ORG-22]
  A6 --> A7[manager tao thoi khoa bieu<br/>SCHED]
  A7 --> DONE[San sang giao bai]
```

## 3. Luồng B — Vòng lặp dạy–học cốt lõi (yêu cầu trung tâm nhất)

```mermaid
flowchart TD
  B1[GV soan/lay noi dung: khoa hoc - practice - exam<br/>COURSE, PRACTICE, EXAM, CONTENT] --> B2[GV giao bai: lop/nhom/ca nhan + deadline<br/>FR-ASSIGN-01..05]
  B2 --> B3[NOTIF bao bai moi + nhac truoc han 24h<br/>FR-NOTIF-06, FR-ASSIGN-14]
  B3 --> B4[HS lam bai tren mobile - autosave<br/>FR-PRACTICE-04..09, FR-EXAM-04..05]
  B4 --> B5{Loai cau?}
  B5 -->|cau dong| B6[Cham tu dong tuc thi<br/>FR-GRADE-01]
  B5 -->|noi/viet| B7[AI cham so bo theo rubric<br/>FR-GRADE-03..04, quota PLAN]
  B7 --> B8[TA cham nhap neu duoc uy quyen<br/>FR-GRADE-08]
  B8 --> B9[GV review + chot diem<br/>FR-GRADE-06..07]
  B6 --> B10
  B9 --> B10[Diem chot do ve bao cao + cong diem gamification<br/>REPORT, FR-GAME-01]
  B10 --> B11[NOTIF tra ket qua cho HS + phu huynh<br/>FR-NOTIF-06]
  B11 --> B12[GV/manager xem bao cao lop - drill-down<br/>FR-REPORT-05..10]
  B12 --> B13[Phu huynh xem ket qua qua cong parent + PDF Zalo<br/>FR-REPORT-23, FR-REPORT-12]
  B12 --> B1
  B4 -.moi thao tac.-> LOG[(activity log<br/>LOG)]
  B9 -.sua diem co before/after.-> LOG
```

Vòng lặp khép kín đúng thiết kế ở [Tầm nhìn §3](01-tam-nhin-san-pham.md): nội dung → giao bài → làm bài → chấm → báo cáo → điều chỉnh lần giao tiếp theo.

## 4. Luồng C — Thi thử tập trung cuối khóa

```mermaid
flowchart LR
  C1[GV tao de tu template ky thi<br/>FR-EXAM-01..03] --> C2[Tao lich thi + phong cho<br/>FR-EXAM-10]
  C2 --> C3[NOTIF bao lich thi HS + phu huynh] --> C4[Ca lop thi dong loat - dong ho server<br/>FR-EXAM-04..05, NFR-PERF-03]
  C4 --> C5[GV giam sat realtime - cap bu gio su co<br/>FR-EXAM-06, FR-EXAM-10..13]
  C5 --> C6[Cham: tu dong + hybrid noi/viet<br/>GRADE] --> C7[Quy doi thang diem chuan + phieu ket qua<br/>FR-EXAM-08..09]
  C7 --> C8[So sanh dau vao - cuoi khoa, bao cao BGH + phu huynh<br/>FR-EXAM-17, REPORT]
```

## 5. Luồng D — Vòng đời nội dung (kho global → tenant)

```mermaid
flowchart LR
  D1[content_editor soan cau hoi/de theo chuan thi<br/>CONTENT, phu luc chuan thi] --> D2[Duyet 4 mat: draft → review → published<br/>FR-CONTENT-10]
  D2 --> D3[Dong goi content pack - phan phoi theo goi<br/>FR-CONTENT, PLAN]
  D3 --> D4[Tenant thay trong kho theo goi - nhan ban ve kho rieng]
  D4 --> D5[teacher/academic_head soan them noi dung tenant<br/>FR-CONTENT-11 - duyet boi academic_head neu bat]
  D5 --> D6[Lap rap practice/exam/khoa hoc tu ngan hang] --> D7[Giao bai - vao Luong B]
```

## 6. Điểm nối giữa các module (hay bị bỏ sót — đã kiểm tra)

| Điểm nối | Cơ chế | Doc |
|---|---|---|
| Nộp bài → trừ quota AI | Kiểm tra quota trước khi enqueue chấm; hết quota → GV chấm tay | GRADE §5.4, PLAN |
| Điểm chốt → báo cáo | Event cập nhật pre-aggregate incremental | REPORT §pipeline |
| Điểm chốt → gamification | Chỉ attempt đầu được cộng điểm; trần điểm/ngày | GAME anti-gaming |
| Điểm danh vắng → Zalo phụ huynh | Digest cuối buổi (đã chốt NOTIF #2) | SCHED, NOTIF |
| Học sinh vào lớp muộn → nhận bài còn hạn | Đã chốt ASSIGN #2 | ASSIGN |
| Sửa điểm sau chốt → log + thông báo | change_reason + audit + activity log + NOTIF | GRADE FR-10, LOG |
| Xóa học sinh → ẩn danh nhưng báo cáo không lệch | Anonymize giữ số liệu thống kê | ORG §5.3, Bảo mật §7 |
| Mọi thao tác ghi → activity log | Interceptor service layer, async | LOG §5.1 |

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-17 | Tạo tài liệu truy vết luồng theo yêu cầu tổng rà soát | Claude |
| 2026-07-17 | Chốt — chuyển trạng thái Đã chốt | Chủ sản phẩm |
