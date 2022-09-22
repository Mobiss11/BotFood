import re

users = [
    ]

def is_new_user(user_id: int) -> bool:
    if user_id in users:
        return False
    return True

def is_phone_valid(phone_number):
    rgx_phone = re.compile("(?:\+?\(?\d{2,3}?\)?\D?)?\d{4}\D?\d{4}")
    if re.findall(rgx_phone, phone_number):
        return True
    return False
