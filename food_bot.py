from contextvars import Context
import logging
import os

from bot_helper import is_new_user
from dotenv import load_dotenv
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

POLICY, REGISTRATION, MENU, CHOOSE_RECIPE, SAVED_RECIPES, PAYMENT, TYPING, AGREED, DISAGREE = range(9)
END = ConversationHandler.END


def policy_acceptance(update, context):
    print('Policy acceptance start')
    text=f"Для начала работы с рецептами необходимо принять пользовательское соглашение на обрботку и хранение персональных данных."
    keyboard = [
        [
            InlineKeyboardButton("Согласен", callback_data=str(AGREED)),
            InlineKeyboardButton("Не согласен", callback_data=str(DISAGREE)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text=text, reply_markup=reply_markup)
    print('out from reg')
    return REGISTRATION


def start(update: Update, context: Context) -> int:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! FoodBot поможет Вам найти блюдо по вкусу")
    logging.info(f'User ID: {update.effective_user.id}')
    if is_new_user(update.effective_user.id):
        policy_acceptance(update, context)
        return POLICY
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"С возвращением, {update.effective_user.first_name}!")
    menu(update, context)
    return MENU

def ask_for_input(update, context):
    print('Ask for input')
    update.callback_query.answer()
    update.callback_query.edit_message_text(text="Ваш номер телефона?")
    context.user_data['phone'] = update.callback_query.data
    print('ask_for_input', update.callback_query.data)
    return TYPING


def menu(update: Update, context: Context):
    keyboard = [
        [
            InlineKeyboardButton("Посмотреть рецепты", callback_data=str(CHOOSE_RECIPE)),
            InlineKeyboardButton("Мои рецепты", callback_data=str(SAVED_RECIPES)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(text="Привет! Погнали!", reply_markup=reply_markup)
    return MENU


def save_input(update, context):
    print("save_input", context.user_data)

    menu(update, context)


def stop(update, context):
    update.callback_query.answer()
    update.callback_query.edit_message_text(text="Всего хорошего!")
    return END


def choose_recipe(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Show recipes here")

    return END


def saved_recipes(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Your recipes")

    return END


def main() -> None:
    print('Main')
    updater = Updater(os.getenv('TG_BOT_TOKEN'))
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            POLICY: [
                CallbackQueryHandler(start, pattern='^' + str(END) + '$')
                ],
            REGISTRATION: [
                
                CallbackQueryHandler(ask_for_input, pattern='^' + str(AGREED) + '$'),
                CallbackQueryHandler(policy_acceptance, pattern='^' + str(DISAGREE) + '$'),

                ],
            TYPING: [MessageHandler(Filters.text & ~Filters.command, save_input)],
            MENU: [
                CallbackQueryHandler(start, pattern='^' + str(END) + '$'),
                CallbackQueryHandler(choose_recipe, pattern='^' + str(CHOOSE_RECIPE) + '$'),
                CallbackQueryHandler(saved_recipes, pattern='^' + str(SAVED_RECIPES) + '$'),
                ],
            CHOOSE_RECIPE: [CallbackQueryHandler(menu, pattern='^' + str(END) + '$')],
            SAVED_RECIPES: [CallbackQueryHandler(menu, pattern='^' + str(END) + '$')],
            TYPING: [MessageHandler(Filters.text & ~Filters.command, save_input)],
            PAYMENT: [
                CallbackQueryHandler(start, pattern='^' + str(END) + '$'), 
                CallbackQueryHandler(menu, pattern='^' + str(END) + '$')
                ],
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
