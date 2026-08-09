from app.config import MAX_TOPIC_LENGTH, SUSPICIOUS_PATTERNS


def validate_topic(topic: str) -> None:
    if not topic.strip():
        raise ValueError("Topic cannot be empty")
    if len(topic) > MAX_TOPIC_LENGTH:
        raise ValueError("Topic is too long")
    lowered = topic.lower()
    if any(p in lowered for p in SUSPICIOUS_PATTERNS):
        raise ValueError("Invalid topic")