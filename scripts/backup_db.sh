#!/usr/bin/env bash
# Backup Postgres của edmicro-app (container edmicro-app-postgres-1).
# - Dump định dạng custom (-Fc) để pg_restore chọn lọc được.
# - Giữ 7 ngày gần nhất, xóa bản cũ hơn.
# Chạy tay:  ./scripts/backup_db.sh
# Tự động:   systemd user timer edmicro-app-backup.timer (02:00 hằng ngày)
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/edmicro-app}"
CONTAINER="edmicro-app-postgres-1"
KEEP_DAYS=7

# Lấy user/db từ .env của repo (không hardcode mật khẩu — pg_dump chạy trong container)
set -a; source "$APP_DIR/.env"; set +a
DB_USER="${POSTGRES_USER:?thiếu POSTGRES_USER trong .env}"
DB_NAME="${POSTGRES_DB:?thiếu POSTGRES_DB trong .env}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$BACKUP_DIR/edmicro-$STAMP.dump"

docker exec "$CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc > "$OUT"

# kiểm tra dump đọc được (liệt kê mục lục) — hỏng thì fail luôn, không giữ file rác
docker exec -i "$CONTAINER" pg_restore --list < "$OUT" > /dev/null

# dọn bản cũ
find "$BACKUP_DIR" -name "edmicro-*.dump" -mtime "+$KEEP_DAYS" -delete

SIZE=$(du -h "$OUT" | cut -f1)
COUNT=$(ls "$BACKUP_DIR"/edmicro-*.dump 2>/dev/null | wc -l)
echo "OK: $OUT ($SIZE) — đang giữ $COUNT bản"
