"""Seed dữ liệu DEMO đầy đủ cho 1 tenant: tài khoản mọi vai trò + dữ liệu để test mọi màn hình.

Chạy:  cd backend && PYTHONPATH=. uv run python ../scripts/seed_demo.py [slug]
       (mặc định slug = b2b; tenant phải đã tồn tại — tạo bằng scripts/seed.py)

Dùng thẳng service layer nên MỌI hiệu ứng phụ chạy thật: chấm tự động, AI chấm writing,
hàng đợi review, thông báo in-app, điểm/streak/huy hiệu, tiến độ khóa học.
Chạy lại lần 2 sẽ báo và thoát (tránh nhân đôi dữ liệu) trừ khi thêm tham số --force.
"""

import asyncio
import sys
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from app.core.security import hash_password
from app.db import SessionLocal, set_tenant
from app.modules.assignment import service as assign_svc
from app.modules.content import service as content_svc
from app.modules.course import service as course_svc
from app.modules.exam import service as exam_svc
from app.modules.game import service as game
from app.modules.notify import service as notify
from app.modules.parent import service as parent_svc
from app.modules.practice import attempt_service as att
from app.modules.practice import service as practice_svc
from app.modules.sched import service as sched_svc
from app.modules.support import service as support_svc

MARKER_BRANCH = "CN Demo Cầu Giấy"

# (username, password, role, họ tên)
USERS = [
    ("manager", "manager123", "manager", "Trần Thị Quản Lý"),
    ("head", "head123", "academic_head", "Lê Tổ Trưởng"),
    ("itadmin", "it123", "it_admin", "Phạm IT"),
    ("teacher", "teacher123", "teacher", "Nguyễn Văn Giáo"),
    ("assistant", "assist123", "assistant", "Đỗ Trợ Giảng"),
    ("content", "content123", "content_editor", "Vũ Nội Dung"),
    ("support", "support123", "support_agent", "Hoàng Hỗ Trợ"),
    ("hs1", "hs123", "student", "Học Sinh An"),
    ("hs2", "hs123", "student", "Học Sinh Bình"),
    ("hs3", "hs123", "student", "Học Sinh Chi"),
    ("parent", "parent123", "parent", "Phụ Huynh An"),
]

BAND_SCALE = [
    {"min": 0, "band": "5.0"},
    {"min": 50, "band": "6.0"},
    {"min": 65, "band": "6.5"},
    {"min": 80, "band": "7.0"},
    {"min": 90, "band": "8.0+"},
]


async def _user(s, tenant_id, username, password, role, full_name) -> str:
    """Tạo user nếu chưa có; trả user id."""
    existing = (
        await s.execute(text("SELECT id FROM users WHERE username = :u"), {"u": username})
    ).scalar_one_or_none()
    if existing:
        return str(existing)
    uid = str(uuid.uuid4())
    await s.execute(
        text(
            "INSERT INTO users (id, tenant_id, username, password_hash, role, full_name, "
            "status, must_change_password) "
            "VALUES (:id, :t, :un, :ph, :r, :fn, 'active', false)"
        ),
        {
            "id": uid,
            "t": tenant_id,
            "un": username,
            "ph": hash_password(password),
            "r": role,
            "fn": full_name,
        },
    )
    return uid


async def _assignee(s, assignment_id: str, student_id: str) -> str:
    return str(
        (
            await s.execute(
                text(
                    "SELECT id FROM assignment_assignees "
                    "WHERE assignment_id = :a AND student_id = :s"
                ),
                {"a": assignment_id, "s": student_id},
            )
        ).scalar_one()
    )


async def _do_assignment(s, tenant_id, assignment_id, student_id, answers_by_type) -> str:
    """HS làm + nộp 1 bài. answers_by_type: dict {loại câu: payload-builder}."""
    aid = await _assignee(s, assignment_id, student_id)
    attempt_id = await att.start_attempt(s, tenant_id, aid, student_id)
    content_id = (
        await s.execute(
            text(
                "SELECT a.content_id FROM assignment_assignees aa "
                "JOIN assignments a ON a.id = aa.assignment_id WHERE aa.id = :a"
            ),
            {"a": aid},
        )
    ).scalar_one()
    practice = await practice_svc.get_practice(s, str(content_id), for_attempt=True)
    for q in practice["questions"]:
        build = answers_by_type.get(q["type"])
        if build is None:
            continue
        await att.save_answer(
            s, tenant_id, attempt_id, student_id, q["question_version_id"], build(q)
        )
    result = await att.submit_attempt(s, tenant_id, attempt_id, student_id)
    # router cộng điểm sau khi nộp → seed gọi lại cho giống app thật
    await game.award_for_submission(s, tenant_id, attempt_id, float(result["score"]))
    return attempt_id


async def main(slug: str, force: bool) -> None:
    async with SessionLocal() as s, s.begin():
        tid = (
            await s.execute(text("SELECT id FROM tenants WHERE slug = :sl"), {"sl": slug})
        ).scalar_one_or_none()
        if tid is None:
            print(f"❌ Chưa có tenant '{slug}'. Chạy trước: uv run python ../scripts/seed.py {slug}")
            return
        tid = str(tid)
        await set_tenant(s, tid)

        seeded = (
            await s.execute(text("SELECT 1 FROM branches WHERE name = :n"), {"n": MARKER_BRANCH})
        ).scalar_one_or_none()
        if seeded and not force:
            print(f"⚠️  Tenant '{slug}' đã có dữ liệu demo. Thêm --force nếu muốn seed lại.")
            return

        # ── 1. Tài khoản mọi vai trò ────────────────────────────
        ids: dict[str, str] = {}
        for un, pw, role, fn in USERS:
            ids[un] = await _user(s, tid, un, pw, role, fn)
        owner_id = (
            await s.execute(text("SELECT id FROM users WHERE username = 'owner'"))
        ).scalar_one()
        owner_id = str(owner_id)

        # ── 2. Chi nhánh + 2 lớp + xếp HS/GV ────────────────────
        bid = str(uuid.uuid4())
        await s.execute(
            text("INSERT INTO branches (id, tenant_id, name, address) VALUES (:b, :t, :n, :a)"),
            {"b": bid, "t": tid, "n": MARKER_BRANCH, "a": "144 Xuân Thủy, Cầu Giấy, Hà Nội"},
        )
        class_ielts, class_toeic = str(uuid.uuid4()), str(uuid.uuid4())
        for cid, name, level in (
            (class_ielts, "IELTS 6.0 — Lớp A", "B2"),
            (class_toeic, "TOEIC Cơ bản — Lớp B", "A2"),
        ):
            await s.execute(
                text(
                    "INSERT INTO classes (id, tenant_id, branch_id, name, language, level) "
                    "VALUES (:c, :t, :b, :n, 'en', :lv)"
                ),
                {"c": cid, "t": tid, "b": bid, "n": name, "lv": level},
            )
        for hs in ("hs1", "hs2", "hs3"):
            await s.execute(
                text(
                    "INSERT INTO class_students (tenant_id, class_id, user_id) VALUES (:t, :c, :u)"
                ),
                {"t": tid, "c": class_ielts, "u": ids[hs]},
            )
        await s.execute(
            text(
                "INSERT INTO class_students (tenant_id, class_id, user_id) VALUES (:t, :c, :u)"
            ),
            {"t": tid, "c": class_toeic, "u": ids["hs3"]},
        )
        for staff, role in (("teacher", "teacher"), ("assistant", "assistant")):
            for cid in (class_ielts, class_toeic):
                await s.execute(
                    text(
                        "INSERT INTO class_staff (tenant_id, class_id, user_id, role) "
                        "VALUES (:t, :c, :u, :r)"
                    ),
                    {"t": tid, "c": cid, "u": ids[staff], "r": role},
                )
        # phụ huynh ↔ con
        await parent_svc.link_child(s, tid, ids["parent"], ids["hs1"], owner_id)

        # ── 3. Ngân hàng câu hỏi (đã xuất bản) ──────────────────
        qids: list[str] = []
        mcq = [
            ("Thủ đô của Việt Nam là?", ["Hà Nội", "TP.HCM", "Đà Nẵng"], 0, "reading"),
            ("'Book' nghĩa là gì?", ["Quyển sách", "Cái bàn", "Cửa sổ"], 0, "reading"),
            ("Chọn câu đúng ngữ pháp:", ["She go to school", "She goes to school"], 1, "reading"),
            ("Nghe và chọn từ đúng:", ["cat", "cut", "cot"], 0, "listening"),
        ]
        for prompt, options, correct, skill in mcq:
            qid = await content_svc.create_question(
                s,
                tid,
                ids["content"],
                {
                    "type": "mcq_single",
                    "language": "en",
                    "skill": skill,
                    "content": {"prompt": prompt, "options": options},
                    "answer_key": {"correct_index": correct},
                },
            )
            await content_svc.publish_question(s, qid)
            qids.append(qid)
        qid_fill = await content_svc.create_question(
            s,
            tid,
            ids["content"],
            {
                "type": "fill_blank",
                "language": "en",
                "skill": "writing",
                "content": {"prompt": "I ___ a student."},
                "answer_key": {"blanks": [["am", "'m"]]},
            },
        )
        await content_svc.publish_question(s, qid_fill)
        qid_writing = await content_svc.create_question(
            s,
            tid,
            ids["content"],
            {
                "type": "writing",
                "language": "en",
                "skill": "writing",
                "content": {
                    "prompt": "Describe your hometown in about 80 words.",
                    "rubric": "IELTS Writing Task 1 — Task Achievement, Coherence, Lexical, Grammar",
                },
                "answer_key": {},
            },
        )
        await content_svc.publish_question(s, qid_writing)

        due_soon = datetime.now(UTC) + timedelta(hours=20)
        due_week = datetime.now(UTC) + timedelta(days=7)

        # ── 4. Practice trắc nghiệm → giao lớp IELTS ────────────
        pid = await practice_svc.create_practice(
            s,
            tid,
            ids["teacher"],
            {
                "name": "Luyện tập Unit 1 — Từ vựng & Ngữ pháp",
                "skill": "reading",
                "language": "en",
                "question_ids": qids[:3] + [qid_fill],
            },
        )
        asg = await assign_svc.create_assignment(
            s, tid, ids["teacher"], {"content_id": pid, "class_id": class_ielts, "due_at": due_soon}
        )
        await notify.notify(
            s,
            tid,
            [ids["hs1"], ids["hs2"], ids["hs3"]],
            notify.EVT_ASSIGNMENT_CREATED,
            "Bài mới được giao",
            "Bạn được giao bài “Luyện tập Unit 1 — Từ vựng & Ngữ pháp”.",
            entity_type="assignment",
            entity_id=asg["id"],
        )

        # ── 5. Practice WRITING → giao (để có bài chờ GV chấm) ──
        pid_w = await practice_svc.create_practice(
            s,
            tid,
            ids["teacher"],
            {
                "name": "Bài viết — Hometown",
                "skill": "writing",
                "language": "en",
                "question_ids": [qid_writing],
            },
        )
        asg_w = await assign_svc.create_assignment(
            s, tid, ids["teacher"], {"content_id": pid_w, "class_id": class_ielts, "due_at": due_week}
        )

        # ── 6. Đề thi có đồng hồ → giao ─────────────────────────
        eid = await exam_svc.create_exam(
            s,
            tid,
            ids["teacher"],
            {
                "name": "Thi thử giữa khóa (30 phút)",
                "skill": "reading",
                "language": "en",
                "question_ids": qids,
                "duration_minutes": 30,
                "band_scale": BAND_SCALE,
            },
        )
        await assign_svc.create_assignment(
            s, tid, ids["teacher"], {"content_id": eid, "class_id": class_ielts, "due_at": due_week}
        )

        # ── 7. Khóa học + bài học → giao lớp ────────────────────
        cid_course = await course_svc.create_course(
            s, tid, ids["teacher"], {"name": "Khóa IELTS Foundation", "language": "en"}
        )
        lessons = []
        for title, kind, body, ref in (
            ("Bài 1 — Giới thiệu khóa học", "text", "Lộ trình 12 buổi, mục tiêu band 6.0.", None),
            ("Bài 2 — Video phát âm cơ bản", "video", "https://example.com/video/phat-am", None),
            ("Bài 3 — Flashcard 50 từ vựng", "flashcard", "Chủ đề: Hometown & Travel", None),
            ("Bài 4 — Luyện tập Unit 1", "practice", "", pid),
        ):
            lessons.append(
                await course_svc.add_lesson(
                    s,
                    tid,
                    cid_course,
                    {"title": title, "kind": kind, "body": body, "content_ref": ref},
                )
            )
        await course_svc.assign_to_class(s, tid, cid_course, class_ielts)

        # ── 8. Mô phỏng hoạt động HS (sinh điểm/thông báo/hàng đợi chấm) ──
        # hs1: làm trắc nghiệm ĐÚNG HẾT → điểm cao + huy hiệu
        correct_map = {
            "mcq_single": lambda q: {
                "selected": {"Thủ đô của Việt Nam là?": 0, "'Book' nghĩa là gì?": 0}.get(
                    q["content"]["prompt"], 1
                )
            },
            "fill_blank": lambda _q: {"blanks": ["am"]},
        }
        await _do_assignment(s, tid, asg["id"], ids["hs1"], correct_map)
        # hs2: làm SAI một phần → điểm trung bình
        await _do_assignment(
            s,
            tid,
            asg["id"],
            ids["hs2"],
            {
                "mcq_single": lambda _q: {"selected": 0},
                "fill_blank": lambda _q: {"blanks": ["is"]},
            },
        )
        # hs3 CHƯA làm → để test nhắc deadline / báo cáo "chưa nộp"

        # hs1 nộp bài WRITING → AI chấm sơ bộ → vào hàng đợi GV chốt
        await _do_assignment(
            s,
            tid,
            asg_w["id"],
            ids["hs1"],
            {
                "writing": lambda _q: {
                    "text": (
                        "My hometown is Hanoi, the capital of Vietnam. It is a busy city with "
                        "many lakes, old streets and delicious street food. Every morning people "
                        "ride motorbikes to work while students walk to school together. I love "
                        "the autumn here because the weather becomes cool and the streets smell "
                        "of milk flowers."
                    )
                }
            },
        )

        # hs1 hoàn thành 2 bài học đầu → tiến độ khóa + điểm
        for lid in lessons[:2]:
            await course_svc.complete_lesson(s, tid, ids["hs1"], lid)

        # ── 9. Lịch học + điểm danh (hs3 vắng → thông báo) ──────
        start = datetime.now(UTC) + timedelta(days=1, hours=11)
        sid_session = await sched_svc.create_session(
            s,
            tid,
            {
                "class_id": class_ielts,
                "starts_at": start,
                "ends_at": start + timedelta(hours=2),
                "topic": "Unit 1 — Vocabulary & Grammar",
                "online_link": "https://meet.google.com/demo-abc",
            },
        )
        past = datetime.now(UTC) - timedelta(days=2)
        sid_past = await sched_svc.create_session(
            s,
            tid,
            {
                "class_id": class_ielts,
                "starts_at": past,
                "ends_at": past + timedelta(hours=2),
                "topic": "Buổi khai giảng",
            },
        )
        await sched_svc.mark_attendance(
            s,
            tid,
            sid_past,
            [
                {"student_id": ids["hs1"], "status": "present"},
                {"student_id": ids["hs2"], "status": "late", "note": "Đến muộn 10 phút"},
                {"student_id": ids["hs3"], "status": "absent", "note": "Không phép"},
            ],
        )

        # ── 10. Nhắc deadline + 1 ticket hỗ trợ ─────────────────
        await notify.remind_due_assignments(s, tid, within_hours=24)
        await support_svc.create_ticket(
            s,
            tid,
            ids["teacher"],
            "Không xuất được báo cáo lớp",
            "Bấm xuất báo cáo lớp IELTS 6.0 thì không thấy phản hồi. Nhờ hỗ trợ kiểm tra.",
        )

    print(f"""
✅ Seed demo xong cho tenant '{slug}'.
   • {len(USERS) + 1} tài khoản (owner + {len(USERS)} vai trò)
   • 1 chi nhánh, 2 lớp, 3 học sinh (hs3 học 2 lớp), GV+trợ giảng gán cả 2 lớp
   • 6 câu hỏi đã xuất bản (4 mcq, 1 điền từ, 1 writing)
   • 1 practice + 1 bài viết + 1 đề thi 30' + 1 khóa học 4 bài — đều đã giao lớp IELTS
   • hs1 nộp đủ (điểm cao + huy hiệu + 2 bài học xong), hs2 nộp một phần, hs3 chưa nộp
   • 1 bài viết đang CHỜ GV CHỐT ĐIỂM (AI đã chấm sơ bộ)
   • 2 buổi học + điểm danh (hs2 muộn, hs3 vắng → có thông báo)
   • Thông báo giao bài + nhắc deadline; 1 ticket hỗ trợ đang mở
""")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    asyncio.run(main(args[0] if args else "b2b", "--force" in sys.argv))
