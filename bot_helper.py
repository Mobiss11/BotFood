users = [
    29292,
    1882690414,
    ]

def is_new_user(user_id: int) -> bool:
    if user_id in users:
        return False
    return True