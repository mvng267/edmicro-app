#!/usr/bin/env python3
"""Seed kho nội dung mẫu PHONG PHÚ cho tenant b2b (chạy được nhiều lần).

Tạo: cây thư mục Ngữ pháp/Từ vựng/Đọc hiểu/Viết + ~70 câu hỏi xuất bản,
7 bài luyện tập, 2 đề thi (có quy đổi band), giao một phần cho Lớp A/Lớp B.
Chạy:  python3 scripts/seed_content.py
"""

import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta

BASE = "http://127.0.0.1:8010/api/v1"
TENANT = "b2b"


def call(method, path, token=None, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Tenant-Slug", TENANT)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=60) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw[:200].decode(errors="replace")


def die(msg):
    print("LỖI:", msg)
    sys.exit(1)


st, r = call("POST", "/authz/login", body={"username": "owner", "password": "owner123"})
if st != 200:
    die(f"login owner: {st} {r}")
TOK = r["access_token"]


# ── thư mục (idempotent theo tên) ─────────────────────────────
def ensure_folder(name, parent_id=None):
    st, flat = call("GET", "/content/folders", TOK)
    for f in flat:
        if f["name"] == name and f.get("parent_id") == parent_id:
            return f["id"]
    st, f = call("POST", "/content/folders", TOK, {"name": name, "parent_id": parent_id})
    if st not in (200, 201):
        die(f"folder {name}: {st} {f}")
    return f["id"]


# ── câu hỏi ───────────────────────────────────────────────────
def mcq(prompt, options, correct, explanation=None, skill="reading", topic=None):
    return {
        "type": "mcq_single",
        "language": "en",
        "skill": skill,
        "topic": topic,
        "content": {"prompt": prompt, "options": options},
        "answer_key": {"correct_index": correct},
        "explanation": explanation,
    }


def blank(prompt, answers, explanation=None, topic=None):
    return {
        "type": "fill_blank",
        "language": "en",
        "skill": "reading",
        "topic": topic,
        "content": {"prompt": prompt},
        "answer_key": {"blanks": [answers]},
        "explanation": explanation,
    }


def writing(prompt, rubric, topic=None):
    return {
        "type": "writing",
        "language": "en",
        "skill": "writing",
        "topic": topic,
        "content": {"prompt": prompt, "rubric": rubric},
        "answer_key": {},
    }


def create_all(folder_id, items, publish=True):
    """Tạo + xuất bản; bỏ qua câu trùng đề bài đã có trong thư mục."""
    st, existing = call("GET", f"/content/questions?folder_id={folder_id}&limit=200", TOK)
    have = {q.get("prompt") for q in existing} if st == 200 else set()
    ids = []
    for it in items:
        if it["content"]["prompt"] in have:
            continue
        it["folder_id"] = folder_id
        st, q = call("POST", "/content/questions", TOK, it)
        if st not in (200, 201):
            die(f"tạo câu: {st} {q}")
        qid = q["id"]
        if publish:
            call("POST", f"/content/questions/{qid}/publish", TOK)
        ids.append(qid)
    return ids


print("== Thư mục ==")
f_gram = ensure_folder("Ngữ pháp")
f_pres = ensure_folder("Thì hiện tại đơn", f_gram)
f_past = ensure_folder("Thì quá khứ đơn", f_gram)
f_fut = ensure_folder("Tương lai & going to", f_gram)
f_cond = ensure_folder("Câu điều kiện & so sánh", f_gram)
f_vocab = ensure_folder("Từ vựng")
f_fam = ensure_folder("Gia đình & bạn bè", f_vocab)
f_school = ensure_folder("Trường học & lớp học", f_vocab)
f_travel = ensure_folder("Du lịch & phương tiện", f_vocab)
f_food = ensure_folder("Ăn uống & nhà hàng", f_vocab)
f_read = ensure_folder("Đọc hiểu")
f_write = ensure_folder("Luyện viết")

print("== Câu hỏi ==")
ids = {}

ids["pres"] = create_all(f_pres, [
    mcq("She ___ to school by bus every day.", ["go", "goes", "going", "gone"], 1,
        "Chủ ngữ ngôi 3 số ít (she) → động từ thêm -es.", topic="present simple"),
    mcq("They ___ football on Sundays.", ["plays", "play", "playing", "played"], 1,
        "Chủ ngữ số nhiều (they) → động từ nguyên mẫu.", topic="present simple"),
    mcq("___ your brother like coffee?", ["Do", "Does", "Is", "Are"], 1,
        "Câu hỏi với ngôi 3 số ít dùng Does.", topic="present simple"),
    mcq("I ___ up at six o'clock every morning.", ["get", "gets", "getting", "got"], 0,
        "Chủ ngữ I → động từ nguyên mẫu.", topic="present simple"),
    mcq("My parents ___ in a small town near Hanoi.", ["lives", "live", "living", "is living"], 1,
        "Chủ ngữ số nhiều (my parents) → live.", topic="present simple"),
    mcq("Water ___ at 100 degrees Celsius.", ["boil", "boils", "boiling", "boiled"], 1,
        "Sự thật hiển nhiên dùng thì hiện tại đơn, water là số ít.", topic="present simple"),
    mcq("He ___ TV in the evening.", ["watch", "watchs", "watches", "watching"], 2,
        "Động từ kết thúc bằng -ch thêm -es.", topic="present simple"),
    mcq("We ___ to the cinema very often.", ["don't go", "doesn't go", "not go", "don't goes"], 0,
        "Phủ định với chủ ngữ we → don't + động từ nguyên mẫu.", topic="present simple"),
])

ids["past"] = create_all(f_past, [
    mcq("Last night, we ___ a very interesting film.", ["watch", "watched", "watches", "watching"], 1,
        "Dấu hiệu last night → quá khứ đơn.", topic="past simple"),
    mcq("She ___ her keys at home this morning.", ["leave", "left", "leaves", "leaving"], 1,
        "Leave là động từ bất quy tắc: leave → left.", topic="past simple"),
    mcq("___ they visit the museum last week?", ["Do", "Does", "Did", "Were"], 2,
        "Câu hỏi quá khứ đơn dùng Did.", topic="past simple"),
    mcq("I ___ breakfast at 7 a.m. yesterday.", ["have", "had", "has", "having"], 1,
        "Have → had (bất quy tắc).", topic="past simple"),
    mcq("He didn't ___ to the party on Saturday.", ["went", "goes", "go", "going"], 2,
        "Sau didn't dùng động từ nguyên mẫu.", topic="past simple"),
    blank("Yesterday I ___ (buy) a new phone.", ["bought"], "Buy → bought.", topic="past simple"),
    blank("They ___ (not/come) to class last Monday.", ["did not come", "didn't come"],
          "Phủ định quá khứ: didn't + V.", topic="past simple"),
])

ids["fut"] = create_all(f_fut, [
    mcq("Look at those clouds! It ___ rain.", ["will", "is going to", "would", "does"], 1,
        "Dự đoán có dấu hiệu rõ ràng → be going to.", topic="future"),
    mcq("I think people ___ on Mars one day.", ["will live", "are living", "live", "lived"], 0,
        "Dự đoán không chắc chắn → will.", topic="future"),
    mcq("We ___ our grandparents next weekend. Everything is planned.",
        ["will visit", "are going to visit", "visit", "visited"], 1,
        "Kế hoạch đã định trước → be going to.", topic="future"),
    mcq("The train ___ at 9:15 tomorrow morning.", ["leaves", "will leaves", "leaving", "left"], 0,
        "Lịch trình cố định dùng hiện tại đơn.", topic="future"),
    mcq("A: The phone is ringing! B: I ___ answer it.", ["am going to", "will", "would", "did"], 1,
        "Quyết định tức thì → will.", topic="future"),
    blank("She ___ (study) abroad next year — she already has the visa.",
          ["is going to study", "'s going to study"], "Kế hoạch chắc chắn → be going to.", topic="future"),
])

ids["cond"] = create_all(f_cond, [
    mcq("If it rains tomorrow, we ___ at home.", ["stay", "will stay", "stayed", "would stay"], 1,
        "Câu điều kiện loại 1: If + hiện tại, will + V.", topic="conditional"),
    mcq("If I ___ rich, I would travel around the world.", ["am", "was", "were", "be"], 2,
        "Câu điều kiện loại 2 dùng were cho mọi ngôi.", topic="conditional"),
    mcq("This book is ___ than that one.", ["interesting", "more interesting", "most interesting", "interestinger"], 1,
        "So sánh hơn với tính từ dài → more + adj.", topic="comparison"),
    mcq("Mount Everest is ___ mountain in the world.", ["higher", "the highest", "highest", "more high"], 1,
        "So sánh nhất: the + adj-est.", topic="comparison"),
    mcq("My sister is ___ me.", ["taller than", "more tall than", "tall than", "the tallest"], 0,
        "Tính từ ngắn: adj-er + than.", topic="comparison"),
    mcq("If you heat ice, it ___.", ["will melt", "melts", "melted", "would melt"], 1,
        "Điều kiện loại 0 (sự thật): If + hiện tại, hiện tại.", topic="conditional"),
])

ids["fam"] = create_all(f_fam, [
    mcq("Your mother's sister is your ___.", ["aunt", "uncle", "cousin", "niece"], 0,
        topic="family"),
    mcq("My father's parents are my ___.", ["uncles", "grandparents", "cousins", "nephews"], 1,
        topic="family"),
    mcq("The daughter of my uncle is my ___.", ["sister", "aunt", "cousin", "niece"], 2,
        topic="family"),
    mcq("A person you know well and like is your ___.", ["neighbor", "friend", "stranger", "boss"], 1,
        topic="family"),
    mcq("Your brother's son is your ___.", ["nephew", "niece", "cousin", "grandson"], 0,
        topic="family"),
    blank("My mother and my father are my ___.", ["parents"], topic="family"),
    blank("The son of your sister is your ___.", ["nephew"], topic="family"),
])

ids["school"] = create_all(f_school, [
    mcq("You write on the whiteboard with a ___.", ["pencil", "marker", "ruler", "eraser"], 1,
        topic="school"),
    mcq("The person who teaches students is a ___.", ["doctor", "teacher", "farmer", "driver"], 1,
        topic="school"),
    mcq("Students do their homework in a ___.", ["notebook", "kitchen", "garden", "car"], 0,
        topic="school"),
    mcq("We borrow books from the school ___.", ["canteen", "library", "gym", "yard"], 1,
        topic="school"),
    mcq("Math, English and History are school ___.", ["subjects", "objects", "projects", "insects"], 0,
        topic="school"),
    blank("We have a fifteen-minute ___ between lessons.", ["break"], topic="school"),
    blank("At the end of term, students take an ___.", ["exam", "examination"], topic="school"),
])

ids["travel"] = create_all(f_travel, [
    mcq("You fly to another country by ___.", ["train", "plane", "bike", "boat"], 1,
        topic="travel"),
    mcq("Before boarding, you must show your ___ at the airport.",
        ["passport", "notebook", "wallet", "menu"], 0, topic="travel"),
    mcq("A place where you stay on holiday is a ___.", ["hospital", "hotel", "school", "office"], 1,
        topic="travel"),
    mcq("In a new city, a ___ helps you find interesting places.",
        ["waiter", "tour guide", "dentist", "pilot"], 1, topic="travel"),
    mcq("You buy a ___ before getting on the train.", ["ticket", "receipt", "letter", "bill"], 0,
        topic="travel"),
    blank("We waited for the bus at the bus ___.", ["stop", "station"], topic="travel"),
])

ids["food"] = create_all(f_food, [
    mcq("In a restaurant, you order food from the ___.", ["map", "menu", "bill", "recipe"], 1,
        topic="food"),
    mcq("The person who serves food in a restaurant is a ___.",
        ["chef", "waiter", "cashier", "guard"], 1, topic="food"),
    mcq("After the meal, you ask for the ___.", ["menu", "ticket", "bill", "spoon"], 2,
        topic="food"),
    mcq("Pho is a famous Vietnamese ___ dish.", ["noodle", "bread", "rice", "salad"], 0,
        topic="food"),
    blank("I'd like a ___ of orange juice, please.", ["glass"], topic="food"),
    blank("The person who cooks food in a restaurant is the ___.", ["chef", "cook"], topic="food"),
])

READING_PASSAGE = (
    "Read the text and answer: \"Minh lives in Da Nang with his parents and his little "
    "sister. Every morning he cycles to school with his best friend Nam. After school, "
    "Minh plays football or goes swimming at the beach. On Sundays, the family visits "
    "their grandmother, who lives in a small village outside the city.\" "
)
ids["read"] = create_all(f_read, [
    mcq(READING_PASSAGE + "Where does Minh live?",
        ["In Hanoi", "In Da Nang", "In a village", "In Hue"], 1, topic="reading"),
    mcq(READING_PASSAGE + "How does Minh go to school?",
        ["By bus", "On foot", "By bicycle", "By car"], 2, topic="reading"),
    mcq(READING_PASSAGE + "What does Minh do after school?",
        ["Plays football or swims", "Watches TV", "Reads books", "Cooks dinner"], 0, topic="reading"),
    mcq(READING_PASSAGE + "Who lives outside the city?",
        ["Minh's sister", "Nam", "Minh's grandmother", "Minh's parents"], 2, topic="reading"),
    mcq(READING_PASSAGE + "When does the family visit their grandmother?",
        ["Every morning", "After school", "On Saturdays", "On Sundays"], 3, topic="reading"),
])

RUBRIC_A2 = "A2 Writing — Nội dung đủ ý, ngữ pháp cơ bản đúng, từ vựng phù hợp, ~80 từ"
ids["write"] = create_all(f_write, [
    writing("Describe your family in about 80 words.", RUBRIC_A2, topic="family"),
    writing("Write about your best friend: appearance, personality, and why you like them. (~80 words)",
            RUBRIC_A2, topic="friend"),
    writing("Describe a typical day at your school. (~80 words)", RUBRIC_A2, topic="school"),
    writing("Write about your favorite food and why you like it. (~80 words)", RUBRIC_A2, topic="food"),
    writing("Describe your last holiday: where you went, what you did. (~100 words)",
            "A2/B1 Writing — dùng thì quá khứ đơn chính xác, kể trình tự rõ ràng", topic="travel"),
    writing("What do you want to do in the future? Write about your plans. (~100 words)",
            "A2/B1 Writing — dùng will/be going to đúng, ý mạch lạc", topic="future"),
])

total = sum(len(v) for v in ids.values())
print(f"Đã tạo mới {total} câu hỏi (câu trùng đề bài được bỏ qua).")

# ── bài luyện tập ─────────────────────────────────────────────
print("== Bài luyện tập ==")
st, practs = call("GET", "/practices", TOK)
have_p = {p["name"] for p in practs} if st == 200 else set()


def folder_qids(fid, status="published"):
    st, qs = call("GET", f"/content/questions?folder_id={fid}&status={status}&limit=200", TOK)
    return [q["id"] for q in qs] if st == 200 else []


def ensure_practice(name, qids, skill=None):
    ex = next((x["id"] for x in (practs or []) if x["name"] == name), None)
    if ex or not qids:
        return ex
    st, p = call("POST", "/practices", TOK, {
        "name": name, "language": "en", "skill": skill, "question_ids": qids,
    })
    if st not in (200, 201):
        die(f"practice {name}: {st} {p}")
    print(" +", name, f"({len(qids)} câu)")
    return p["id"]


p_ids = {}
p_ids["pres"] = ensure_practice("Ngữ pháp — Thì hiện tại đơn", folder_qids(f_pres))
p_ids["past"] = ensure_practice("Ngữ pháp — Thì quá khứ đơn", folder_qids(f_past))
p_ids["fut"] = ensure_practice("Ngữ pháp — Tương lai & going to", folder_qids(f_fut))
p_ids["vocab1"] = ensure_practice(
    "Từ vựng — Gia đình & trường học", folder_qids(f_fam) + folder_qids(f_school))
p_ids["vocab2"] = ensure_practice(
    "Từ vựng — Du lịch & ăn uống", folder_qids(f_travel) + folder_qids(f_food))
p_ids["read"] = ensure_practice("Đọc hiểu — Một ngày của Minh", folder_qids(f_read), skill="reading")
w_all = folder_qids(f_write)
p_ids["write1"] = ensure_practice("Luyện viết — My Family", w_all[:1], skill="writing")
p_ids["write2"] = ensure_practice("Luyện viết — My Last Holiday", w_all[4:5], skill="writing")

# ── đề thi ────────────────────────────────────────────────────
print("== Đề thi ==")
st, exams = call("GET", "/exams", TOK)
have_e = {e["name"] for e in exams} if st == 200 else set()


def ensure_exam(name, qids, minutes, band_scale):
    ex = next((x["id"] for x in (exams or []) if x["name"] == name), None)
    if ex or not qids:
        return ex
    st, e = call("POST", "/exams", TOK, {
        "name": name, "language": "en", "question_ids": qids,
        "duration_minutes": minutes, "band_scale": band_scale,
    })
    if st not in (200, 201):
        die(f"exam {name}: {st} {e}")
    print(" +", name, f"({len(qids)} câu, {minutes} phút)")
    return e["id"]


mix20 = (folder_qids(f_pres)[:5] + folder_qids(f_past)[:4] + folder_qids(f_fut)[:3]
         + folder_qids(f_cond)[:3] + folder_qids(f_read)[:5])
e1 = ensure_exam("Thi thử A2 cuối khóa (30 phút)", mix20, 30, [
    {"min": 0.0, "band": "A1"}, {"min": 0.35, "band": "A2-"},
    {"min": 0.5, "band": "A2"}, {"min": 0.7, "band": "A2+"},
    {"min": 0.85, "band": "B1"},
])
gram10 = folder_qids(f_cond) + folder_qids(f_fut)[:4]
e2 = ensure_exam("Kiểm tra 15 phút — Ngữ pháp", gram10[:10], 15, [
    {"min": 0.0, "band": "Chưa đạt"}, {"min": 0.5, "band": "Đạt"},
    {"min": 0.7, "band": "Khá"}, {"min": 0.9, "band": "Giỏi"},
])

# ── giao bài cho Lớp A / Lớp B ────────────────────────────────
print("== Giao bài ==")
st, classes = call("GET", "/org/classes", TOK)
classes = classes if st == 200 else []


def find_class(part):
    return next((c["id"] for c in classes if part in c["name"]), None)
due = (datetime.now(UTC) + timedelta(days=7)).isoformat()

st, assigns = call("GET", "/assignments", TOK)
have_a = {(a.get("content_id"), a.get("class_id")) for a in assigns} if st == 200 else set()


def assign(content_id, class_name):
    cid = find_class(class_name)
    if not content_id or not cid or (content_id, cid) in have_a:
        return
    st, a = call("POST", "/assignments", TOK,
                 {"content_id": content_id, "class_id": cid, "due_at": due})
    if st in (200, 201):
        print(f" + giao {content_id[:8]}… cho {class_name} ({a.get('assignee_count')} HS)")


for key in ("pres", "past", "vocab1", "read", "write1"):
    assign(p_ids.get(key), "Lớp A")
for key in ("fut", "vocab2", "write2"):
    assign(p_ids.get(key), "Lớp B")
assign(e1, "Lớp A")
assign(e2, "Lớp B")

print("XONG ✅")
