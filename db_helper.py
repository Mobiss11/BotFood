import os
import psycopg2

from dotenv import load_dotenv
from models import User, Meal, Ingredient

load_dotenv()


def connect_db() -> psycopg2.connect:
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )


def get_user(telegram_user_id: int) -> User:
    user = None
    sql = f"SELECT \
              id,\
              telegram_user_id, \
              telegram_user_name, \
              policy_accepted, \
              user_phone_number \
            FROM public.telegram_user_profile \
            WHERE telegram_user_id = {telegram_user_id} limit 1"
    try:
        connect = connect_db()
        cur = connect.cursor()
        cur.execute(sql)
        user_records = cur.fetchall()
        for user_record in user_records:
            user = User(
                id=user_record[0],
                user_id = user_record[1],
                user_name = user_record[2],
                policy_accepted = user_record[3],
                phone_number = user_record[4]
                )
            break
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connect is not None:
            connect.close()
    return user    


def add_user(user: User) -> int:
    if get_user(user.user_id):
        return update_user(user)
    id = None
    connect = None
    sql_user_name = f"'{user.user_name}'" if user.user_name else 'NULL'
    sql_phone_number = f"'{user.phone_number}'" if user.phone_number else 'NULL'
    sql = f"INSERT INTO public.telegram_user_profile \
    (telegram_user_id, telegram_user_name, policy_accepted, user_phone_number)\
    VALUES ({user.user_id}, {sql_user_name}, {user.policy_accepted}, {sql_phone_number})\
    RETURNING id;"    
    try:
        connect = connect_db()
        cur = connect.cursor()
        cur.execute(sql)
        id = cur.fetchone()[0]
        connect.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connect is not None:
            connect.close()
    return user.id


def update_user(user:User) -> int:
    if not get_user(user.user_id):
        return add_user(user)
    connect = None
    sql_user_name = f"'{user.user_name}'" if user.user_name else 'NULL'
    sql_phone_number = f"'{user.phone_number}'" if user.phone_number else 'NULL'
    sql = f"UPDATE public.telegram_user_profile \
              set telegram_user_name = {sql_user_name}, \
                  policy_accepted = {user.policy_accepted}, \
                  user_phone_number = {sql_phone_number}\
            WHERE telegram_user_id = {user.user_id};"  
    try:
        connect = connect_db()
        cur = connect.cursor()
        cur.execute(sql)
        connect.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connect is not None:
            connect.close()
    return user.user_id


def get_ingredients(meal_id: int) -> list[Ingredient]:
    ingredients = []
    sql = f"SELECT \
              ingredient, \
              amount, \
              measure \
            FROM public.recipes \
            WHERE meal_id = {meal_id}"
    try:
        connect = connect_db()
        cur = connect.cursor()
        cur.execute(sql)
        ingredient_records = cur.fetchall()
        for ingredient_record in ingredient_records:
            ingredient = Ingredient(
                name=ingredient_record[0], 
                amount=ingredient_record[1],
                measure=ingredient_record[2])
            ingredients.append(ingredient)
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connect is not None:
            connect.close()
    return ingredients


def get_meals(user: User, limit: int = 10, offset: int = 0, is_favorite: bool = False) -> list[Meal]:
    meals = []
    if limit > 100:
        limit = 100
    sql = "SELECT \
              id, \
              name, \
              description, \
              manual, \
              image_url \
            FROM public.foodadminapp_meal fm "
    if is_favorite:
        sql += f" WHERE exists (select 1 \
                                    from public.foodadminapp_likemeals lm \
                                    where lm.user_id = {user.id} \
                                      and \"like\" = 'Like' \
                                      and lm.meal_id = fm.id )"      
    else:  
        sql += f"WHERE not exists (select 1 \
                                    from public.foodadminapp_likemeals lm \
                                    where lm.meal_id = fm.id \
                                    and lm.user_id = {user.id})"
    sql += f" limit {limit} offset {offset} "
    try:
        connect = connect_db()
        cur = connect.cursor()
        cur.execute(sql)
        meal_records = cur.fetchall()
        for meal_record in meal_records:
            meal = Meal(
                id=meal_record[0],
                name=meal_record[1],
                description=meal_record[2],
                manual=meal_record[3],
                image_url=meal_record[4],
                ingredients=get_ingredients(meal_id=meal_record[0])
                )
            meals.append(meal)
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connect is not None:
            connect.close()
    return meals


def set_like(user_id, meal_id, like='Like'):
    connect = None
    sql = f"INSERT INTO public.foodadminapp_likemeals \
    (user_id, meal_id, \"like\")\
    VALUES ({user_id}, {meal_id}, '{like}')\
    RETURNING user_id;"    
    try:
        connect = connect_db()
        cur = connect.cursor()
        cur.execute(sql)
        id = cur.fetchone()[0]
        connect.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connect is not None:
            connect.close()
    return id


def get_favorite_total(user_id):
    ingredients = []
    sql = f"SELECT \
              count(*) \
            FROM public.foodadminapp_likemeals \
            WHERE \"like\" = 'Like' and user_id = {user_id}"
    try:
        connect = connect_db()
        cur = connect.cursor()
        cur.execute(sql)
        total = cur.fetchall()[0][0]
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connect is not None:
            connect.close()
    return total


if __name__ == '__main__':
    print(get_favorite_total(6))
