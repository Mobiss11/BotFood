from contextvars import Context
import logging
import os

from bot_helper import is_phone_valid, get_recipe
from db_helper import add_user, update_user, get_user, get_meals, set_like, get_favorite_total
from dotenv import load_dotenv
from models import User, Meal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
)


load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

REGISTRATION, MENU, RECIPE = range(3)
(
    CHOOSE_RECIPE,
    FAVORITE_RECIPES,
    PAYMENT,
    TYPING,
    ACCEPT,
    DECLINE,
    START_OVER,
    LIKE,
    DISLIKE,
    BACK,
    NEXT,
) = range(11)
END = ConversationHandler.END
DB_LIMIT = 3
MAX_FREE_LIKES = 3


def start(update: Update, context: Context) -> int:
    logging.info(f'User ID: {update.effective_user.id}')
    user = get_user(update.effective_user.id)

    if not user:
        user = User(id=None, user_id=update.effective_user.id)
        user.id = add_user(user)
    context.user_data['user'] = user
    context.user_data['total_fav_meals'] = get_favorite_total(user.id)
    logging.info(f"User ID: {update.effective_user.id} - favorite total = {context.user_data['total_fav_meals']}")
    if not user.policy_accepted:
        return policy_acceptance(update, context)
    elif not user.phone_number:
        context.user_data['instance'] = MENU
        return ask_for_phone(update, context)
    return menu(update, context)


def policy_acceptance(update: Update, context: Context) -> int:
    text = f"Для начала работы с рецептами необходимо принять <a href=\"{os.getenv('POLICY_ADDRESS')}\">\
пользовательское соглашение</a> на обрботку и хранение персональных данных."
    keyboard = [
        [
            InlineKeyboardButton("Согласен", callback_data=str(ACCEPT)),
            InlineKeyboardButton("Не согласен", callback_data=str(DECLINE)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if context.user_data.get(START_OVER):
        update.callback_query.answer()
    else:
        update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

    context.user_data[START_OVER] = False
    return REGISTRATION


def accept_policy(update: Update, context: Context) -> int:
    query = update.callback_query
    query.answer()
    logging.info(f'User ID: {update.effective_user.id} - accepted a policy')
    context.user_data['user'].policy_accepted = True
    update_user(context.user_data['user'])
    return ask_for_phone(update, context)


def decline_policy(update: Update, context: Context) -> int:
    context.user_data[START_OVER] = True
    logging.info(f'User ID: {update.effective_user.id} - declined a policy')
    return policy_acceptance(update, context)


def ask_for_phone(update: Update, context: Context) -> int:
    text = "Введите Ваш номер телефона:"
    logging.info(f'User ID: {update.effective_user.id} - ask a phone number')
    if context.user_data.get('instance') == MENU:
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    else:
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text)

    return TYPING


def save_phone(update: Update, context: Context) -> int:
    phone_number = update.message.text
    if is_phone_valid(phone_number):
        context.user_data['user'].phone_number = phone_number
        update_user(context.user_data['user'])
        context.user_data['instance'] = RECIPE
        return menu(update, context)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Вы ввели не валидный номер телефона. Попробуйте еще.")
    logging.info(f'User ID: {update.effective_user.id} - wrong phone number{phone_number}')
    return ask_for_phone(update, context)


def menu(update: Update, context: Context) -> int:
    keyboard = [
        [
            InlineKeyboardButton("Посмотреть рецепты", callback_data=str(CHOOSE_RECIPE)),
            InlineKeyboardButton("Мои рецепты", callback_data=str(FAVORITE_RECIPES)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text="Выберите, что будем делать дальше:", reply_markup=reply_markup)
    logging.info(f'User ID: {update.effective_user.id} - in Menu')
    return MENU


def load_meal(update: Update, context: Context) -> Meal:
    logging.info(f'User ID: {update.effective_user.id} - uploading meal...')
    if not context.user_data.get('offset'):
        context.user_data['offset'] = 0
    if not context.user_data.get('meals'):
        context.user_data['meals'] = get_meals(context.user_data['user'], DB_LIMIT, context.user_data['offset'])
    if not context.user_data.get('meals') and context.user_data['offset'] > 0:
        context.user_data['offset'] = 0
        return load_meal(update, context)
    if not context.user_data.get('meals'):
        return None
    meal = context.user_data['meals'][0]
    del context.user_data['meals'][0]
    context.user_data['offset'] += 1
    context.user_data['current_meal'] = meal
    return meal


def load_favorite_meal(update: Update, context: Context) -> Meal:
    logging.info(f'User ID: {update.effective_user.id} - uploading favorite meal...')
    if not context.user_data.get('fav_offset'):
        context.user_data['fav_offset'] = 0
    if context.user_data['fav_offset'] < 0:
        context.user_data['fav_offset'] = 0
    offset = context.user_data['fav_offset']
    if not context.user_data.get('total_fav_meals'):
        context.user_data['total_fav_meals'] = get_favorite_total(context.user_data['user'].id)
    total = context.user_data['total_fav_meals']
    if not context.user_data.get('fav_meals'):
        context.user_data['fav_meals'] = get_meals(context.user_data['user'], DB_LIMIT, offset, is_favorite=True)
        if not context.user_data.get('fav_meals'):
            return None
    elif offset == len(context.user_data['fav_meals']) and offset < total:
        context.user_data['fav_meals'] += get_meals(context.user_data['user'], DB_LIMIT, offset, is_favorite=True)
    meal = context.user_data['fav_meals'][offset]
    if offset + 1 == total:
        context.user_data['fav_offset'] = -1
    return meal


def choose_recipe(update: Update, context: Context) -> int:
    logging.info(f'User ID: {update.effective_user.id} - All Recipes')
    meal = load_meal(update, context)
    if meal:
        text = get_recipe(meal)
        keyboard = [
            [
                InlineKeyboardButton("👍 Нравится", callback_data=str(LIKE)),
                InlineKeyboardButton("👎 Не нравится", callback_data=str(DISLIKE)),
            ],
            [
                InlineKeyboardButton("💗 Мои рецепты", callback_data=str(FAVORITE_RECIPES)),
            ]
        ]
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=meal.image_url, caption=f"{meal.name}\n{meal.description}")
    else:
        text = "По Вашему запросу ничего не найдено."
        keyboard = [
            [
                InlineKeyboardButton("💗 Мои рецепты", callback_data=str(FAVORITE_RECIPES)),
            ]
        ]
    query = update.callback_query
    query.answer()
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
    return RECIPE


def favorite_recipes(update: Update, context: Context) -> int:
    logging.info(f'User ID: {update.effective_user.id} - Favorite recipes')
    meal = load_favorite_meal(update, context)
    if meal:
        text = get_recipe(meal)
        keyboard = [
            [
                InlineKeyboardButton("⬅ Предыдуший", callback_data=str(BACK)),

            ],
            [
                InlineKeyboardButton("🍲 Все рецепты", callback_data=str(CHOOSE_RECIPE)),
            ]
        ]
        if context.user_data.get('fav_offset') is None or context.user_data.get('fav_offset') == 0:
            del keyboard[0][0]
        if context.user_data.get('fav_offset') == -1:
            keyboard[0].append(InlineKeyboardButton("В начало 😋", callback_data=str(NEXT)))
        else:
            keyboard[0].append(InlineKeyboardButton("Следующий ➡", callback_data=str(NEXT)))
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=meal.image_url, caption=f"{meal.name}\n{meal.description}")
    else:
        text = "По Вашему запросу ничего не найдено."
        keyboard = [
            [
                InlineKeyboardButton("🍲 Все рецепты", callback_data=str(CHOOSE_RECIPE)),
            ]
        ]
    query = update.callback_query
    query.answer()
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
    return RECIPE


def like_recipe(update: Update, context: Context) -> int:
    logging.info(f'User ID: {update.effective_user.id} - like recipe')
    set_like(context.user_data['user'].id, context.user_data['current_meal'].id)
    if not context.user_data.get('total_fav_meals'):
        context.user_data['total_fav_meals'] = 1
    else:
        context.user_data['total_fav_meals'] += 1
    if not context.user_data.get('fav_meals'):
        context.user_data['fav_meals'] = []
    context.user_data['fav_meals'].append(context.user_data['current_meal'])
    return choose_recipe(update, context)


def dislike_recipe(update: Update, context: Context) -> int:
    logging.info(f'User ID: {update.effective_user.id} - dislike recipe')
    set_like(context.user_data['user'].id, context.user_data['current_meal'].id, 'Dislike')
    return choose_recipe(update, context)


def next_recipe(update: Update, context: Context) -> int:
    logging.info(f'User ID: {update.effective_user.id} - next recipe')
    context.user_data['fav_offset'] += 1
    return favorite_recipes(update, context)


def previous_recipe(update: Update, context: Context) -> int:
    logging.info(f'User ID: {update.effective_user.id} - previous recipe')
    context.user_data['fav_offset'] -= 1
    return favorite_recipes(update, context)


def stop(update: Update, context: Context) -> int:
    logging.info(f'User ID: {update.effective_user.id} - stop commend received')
    update.message.reply_text('До новых встреч!')
    return END


def main() -> None:
    updater = Updater(os.getenv('TG_BOT_TOKEN'))
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            REGISTRATION: [
                CallbackQueryHandler(accept_policy, pattern='^' + str(ACCEPT) + '$'),
                CallbackQueryHandler(decline_policy, pattern='^' + str(DECLINE) + '$'),
                ],
            MENU: [
                CallbackQueryHandler(start, pattern='^' + str(END) + '$'),
                CallbackQueryHandler(choose_recipe, pattern='^' + str(CHOOSE_RECIPE) + '$'),
                CallbackQueryHandler(favorite_recipes, pattern='^' + str(FAVORITE_RECIPES) + '$'),
                ],
            RECIPE: [
                CallbackQueryHandler(like_recipe, pattern='^' + str(LIKE) + '$'),
                CallbackQueryHandler(dislike_recipe, pattern='^' + str(DISLIKE) + '$'),
                CallbackQueryHandler(favorite_recipes, pattern='^' + str(FAVORITE_RECIPES) + '$'),
                CallbackQueryHandler(choose_recipe, pattern='^' + str(CHOOSE_RECIPE) + '$'),
                CallbackQueryHandler(next_recipe, pattern='^' + str(NEXT) + '$'),
                CallbackQueryHandler(previous_recipe, pattern='^' + str(BACK) + '$'),
                ],
            TYPING: [MessageHandler(Filters.text & ~Filters.command, save_phone)],
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    dispatcher.add_handler(conv_handler)

    if os.getenv('ENVIRONMENT') in ('PRODUCTION', 'UAT'):
        updater.start_webhook(listen="0.0.0.0",
                              port=int(os.environ.get('PORT', 5000)),
                              url_path=os.getenv('TG_BOT_TOKEN'),
                              webhook_url='https://telegram-food-bot-dev.herokuapp.com/' + os.getenv('TG_BOT_TOKEN')
                              )
    else:
        updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
