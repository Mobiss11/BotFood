# BotFood

To start with TG Bot do the following.

## Make sure Python 3 is installed

## Set up a virtual environment, settings and install dependencies

### Settings

Create file .env with key TG_BOT_TOKEN.

```bash
TG_BOT_TOKEN='your_token_from_BotFather'
```

### Virtual  environment example

### Install dependencies

```bash
pip install -r requirements
```

### Run script food_bot.pyc

## Files

### food_bot.py

The main logic of the Bot.

### bot_helper.py

Helper functions:

is_new_user - to check if should register user.
is_phone_valid - check phone number by regular expression
