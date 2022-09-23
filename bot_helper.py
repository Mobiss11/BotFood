import re
import settings

users = [
    ]

def is_new_user(user_id: int) -> bool:
    if user_id in users:
        return False
    return True

def is_phone_valid(phone_number: str) -> bool:
    rgx_phone = re.compile(settings.PHONE_NUMBER_REGEX)
    if re.findall(rgx_phone, phone_number):
        return True
    return False
