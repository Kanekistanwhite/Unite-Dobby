from config.settings import LEADER_USER_IDS


def is_approved_leader(user_id: int | None) -> bool:
    """Return True when the Telegram user is an approved leader."""
    if user_id is None:
        return False

    return user_id in LEADER_USER_IDS