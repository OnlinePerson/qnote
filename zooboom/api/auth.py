import hashlib
import hmac
import urllib.parse
import time
import json
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")


def verify_init_data(init_data: str) -> dict | None:
    if not BOT_TOKEN:
        return {"id": 0, "first_name": "Dev", "username": "dev_user"}

    try:
        parsed = urllib.parse.parse_qs(init_data, keep_blank_values=True)
        hash_val = parsed.pop("hash", [None])[0]
        if not hash_val:
            return None

        auth_date = int(parsed.get("auth_date", [0])[0])
        if time.time() - auth_date > 86400:
            return None

        data_check_string = "\n".join(
            f"{k}={v[0]}" for k, v in sorted(parsed.items())
        )

        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected, hash_val):
            return None

        user_raw = parsed.get("user", [None])[0]
        if not user_raw:
            return None

        return json.loads(user_raw)

    except Exception:
        return None
