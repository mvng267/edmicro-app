"""Adapter kênh gửi. Xem SRS NOTIF §5. M8: in-app thật (ghi DB); email/ZNS/SMS stub (log)
— nối provider thật ở slice sau. In-app luôn là bản ghi thông báo bền vững."""

import logging

logger = logging.getLogger("notify")

# Kênh trả phí (ZNS/SMS) ở M8 chỉ log — chưa nối OA/nhà mạng.
STUB_CHANNELS = {"email", "zns", "sms"}


def deliver_stub(channel: str, user_id: str, title: str, body: str) -> None:
    """Giả lập gửi kênh ngoài (email/ZNS/SMS) — ghi log để kiểm chứng, không gọi mạng."""
    logger.info("notify[%s] -> user=%s :: %s | %s", channel, user_id, title, body)
