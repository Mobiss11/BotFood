import os
from dotenv import load_dotenv
from telegram import LabeledPrice
from telegram.ext import Updater, CommandHandler


def make_payment(update, context):
    """ В amount ставим сумму в копейках
        В provider_token ставим токен Ю-мани или кого то другого подключив бота в BotFather к провайдеру платежей"""
    price = LabeledPrice(label='Руб', amount=100000)
    context.bot.sendInvoice(
        chat_id=update.effective_chat.id,
        description='Подписка на рецепты',
        provider_token=provider_token,
        currency='RUB',
        prices=[price],
        title='Подписка на рецепты',
        payload='some-invoice-payload-for-our-internal-use',
    )


def main():
    load_dotenv()
    telegram_token = os.environ.get('TELEGRAM_TOKEN')
    provider_token = os.environ.get('PROVIDER_TOKEN')

    updater = Updater(token=telegram_token)
    dispatcher = updater.dispatcher

    invoice_handler = CommandHandler('invoice', make_payment)

    dispatcher.add_handler(invoice_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
