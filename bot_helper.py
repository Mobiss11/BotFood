import re

from models import Meal


def is_phone_valid(phone_number):
    rgx_phone = re.compile(r"((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}")
    if re.findall(rgx_phone, phone_number):
        return True
    return False


def get_recipe(meal: Meal) -> str:
    recipe = f"{meal.name}\n\n"
    recipe += "ИНГРЕДИЕНТЫ\n"
    for ingredient in meal.ingredients:
        recipe += f"{ingredient.name} - {ingredient.amount} {ingredient.measure}\n"
    recipe += "\nИНСТРУКЦИЯ ПРИГОТОВЛЕНИЯ\n"
    recipe += meal.manual
    return recipe
