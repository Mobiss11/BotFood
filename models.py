from turtle import title


class User():

    def __init__(self, id: int, user_id: int, user_name: str = None, policy_accepted:bool = False, phone_number:str = None) -> None:
        self.id = id
        self.user_id = user_id
        self.user_name = user_name
        self.policy_accepted = policy_accepted
        self.phone_number = phone_number
        
    def __str__(self) -> str:
        return f"class({self.__class__.__name__}) {self.user_id}: {self.user_name}"


class Ingredient():

    def __init__(self, name: str, amount: float, measure: str) -> None:
        self.name = name
        self.amount = amount
        self.measure = measure

    def __str__(self) -> str:
        return f"Class({self.__class__.__name__})"


class Meal():

    def __init__(self, id:int, name: str, description:str, manual:str, image_url:str, ingredients: list[Ingredient]) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.manual = manual
        self.image_url = image_url
        self.ingredients = ingredients

    def __str__(self) -> str:
        return f"Class({self.__class__.__name__}) {self.id}: {self.name}"
