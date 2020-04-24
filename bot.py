import logging
import json
import telegram
from uuid import uuid4
from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import praw
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logger = logging.getLogger('Reddit')
    logger.setLevel(logging.INFO)
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    logger.addHandler(sh)

    req_body = req.get_body()
    logger.info(req_body)
    bot = telegram.Bot('botid:sec-ret')

    update = telegram.Update.de_json(json.loads(req_body), bot)

    if update.inline_query is not None:
        query = update.inline_query.query
        results = [
            InlineQueryResultArticle(
                id=uuid4(),
                title="Days",
                input_message_content=InputTextMessageContent("{} days".format(query))),
            InlineQueryResultArticle(
                id=uuid4(),
                title="Minutes",
                input_message_content=InputTextMessageContent("{} minutes".format(query)))]
    
        update.inline_query.answer(results, cache_time=0, is_personal=True)
        return func.HttpResponse(f"Hello!")

    chat_id = update.message.chat.id
    text = update.message.text

    if text == '/start':
        text = """Hello, human! I am an reddit embedder bot. Just provide me reddit url and I'll try to get media content and embed it to the telegram message!"""
    else:
        text = process_message(update.message.text)

    bot.sendMessage(chat_id=chat_id, text=text)
    return func.HttpResponse(f"Hello!")

def process_message(text):
    try:
        reddit = praw.Reddit(client_id='reddit_client_id',client_secret="secret",refresh_token='refresh_token',user_agent='telegram-embedder-for-reddit-script by u/AlexChern0v')
        thing = reddit.submission(url=text)
    except:
        return "Something went wrong, check the url provided and try again later."
    return process_submission(thing)

def process_submission(thing):
    media = thing.media
    if media is None:
        ret = thing.url
        logging.info(f"No media. Req: {thing.id}, Ret: {ret}")
        return ret
    if 'reddit_video' in thing.media:
        ret = thing.media['reddit_video']['fallback_url']
        logging.info(f"reddit_video. Req: {thing.id}, ret: {ret}")
        return ret
    return non_video_fallback(thing)

def non_video_fallback(thing):
    media = thing.media
    if 'oembed' in media:
        oembed_type = media['type']
        if oembed_type == 'imgur.com':
            ret = media['oembed']['thumbnail_url']
            logging.info(f"imgur.com. Req: {thing.id}, ret: {ret}")
        elif oembed_type == 'gfycat.com':
            ret = thing.url
            logging.info(f"gfycat.com. Req: {thing.id}, ret: {ret}")
        else:
            ret = thing.url
            logging.info(f"unknown oem. Req: {thing.id}, ret: {ret}")
        return ret
    else:
        ret = thing.url
        logging.info(f"unknown oem. Req: {thing.id}, ret: {ret}")
        return ret
