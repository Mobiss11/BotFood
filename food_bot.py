from contextvars import Context
import logging
import os
import datetime

from bot_helper import is_new_user, is_phone_valid, users
from dotenv import load_dotenv
from pathlib import Path
from recipes import recipe_text
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
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


def start(update: Update, context: Context) -> int:
    logging.info(f'User ID: {update.effective_user.id}')
    if is_new_user(update.effective_user.id):
        return policy_acceptance(update, context) 
    return menu(update, context)


def policy_acceptance(update, context):
    text=f"Для начала работы с рецептами необходимо принять <a href=\"https://example.com/\">пользовательское соглашение</a> на обрботку и хранение персональных данных."
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


def accept_policy(update, context):
    query = update.callback_query
    query.answer()
    logging.info(f'User ID: {update.effective_user.id} - accepted a policy')
    return ask_for_phone(update, context)


def decline_policy(update, context):
    context.user_data[START_OVER] = True
    logging.info(f'User ID: {update.effective_user.id} - declined a policy')
    return  policy_acceptance(update, context) 


def ask_for_phone(update, context):
    update.callback_query.answer()
    update.callback_query.edit_message_text(text="Ваш номер телефона?")
    return TYPING


def save_phone(update: Update, context: Context):
    phone_number = update.message.text
    if is_phone_valid(phone_number):
        users.append(update.effective_user.id)
        return menu(update, context)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Your phone number is not valid, please try again")
    
    return ask_for_phone(update, context)


def menu(update: Update, context: Context):
    keyboard = [
        [
            InlineKeyboardButton("Посмотреть рецепты", callback_data=str(CHOOSE_RECIPE)),
            InlineKeyboardButton("Мои рецепты", callback_data=str(FAVORITE_RECIPES)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text="Выберите, что будем делать дальше:", reply_markup=reply_markup)
    return MENU


def choose_recipe(update, context):
    text = f"{recipe_text}\n\n({datetime.datetime.now()})"
    query = update.callback_query
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("👍 Нравится", callback_data=str(LIKE)),
            InlineKeyboardButton("👎 Не нравится", callback_data=str(DISLIKE)),
        ],
        [
            InlineKeyboardButton("💗 Мои рецепты", callback_data=str(FAVORITE_RECIPES)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    with open(Path.cwd() / 'images' / 'rid_2.jpg', 'rb') as file:
        query.message.edit_media(
            media=InputMediaPhoto(
                media=file,
                caption=text[:1024]
            ),
            reply_markup=reply_markup,
            parse_mode='HTML'
            )

    return RECIPE


def like_recipe(update: Update, context: Context) -> int:
    return choose_recipe(update, context)


def dislike_recipe(update: Update, context: Context) -> int:
    return choose_recipe(update, context)


def favorite_recipes(update, context):
    text = f"{recipe_text}\n\n({datetime.datetime.now()})"
    query = update.callback_query
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("⬅ Предыдуший", callback_data=str(BACK)),
            InlineKeyboardButton("Следующий ➡", callback_data=str(NEXT)),
        ],
        [
            InlineKeyboardButton("🍲 Все рецепты", callback_data=str(CHOOSE_RECIPE)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    with open(Path.cwd() / 'images' / 'rid_2.jpg', 'rb') as file:
        query.message.edit_media(
            media=InputMediaPhoto(
                media=file,
                caption=text[:1024]
            ),
            reply_markup=reply_markup,
            parse_mode='HTML'
            )

    return RECIPE


def next_recipe(update: Update, context: Context) -> int:
    return END


def previous_recipe(update: Update, context: Context) -> int:
    return END


def stop(update, context):
    update.message.reply_text('До новых встреч!')
    return END


def main() -> None:
    print('Main')
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

    updater.start_webhook(listen="0.0.0.0",
                        port=int(os.environ.get('PORT', 5000)),
                        url_path=os.getenv('TG_BOT_TOKEN'),
                        webhook_url= 'https://telegram-food-bot-dev.herokuapp.com/' + os.getenv('TG_BOT_TOKEN')
                        )
    updater.idle()


if __name__ == '__main__':
    main()
