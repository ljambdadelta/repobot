#!/usr/local/bin/python3.10
from email.mime import message
import logging
import os
import asyncio
import ast
#TODO: stats
#TODO: enable/disable source parsing: VK, TWitter, etc. Account-based or direct posting? RSS?
from aiogram import Bot, Dispatcher, executor, types, filters
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram_media_group import media_group_handler
from aiogram.dispatcher.filters import BoundFilter

class MyFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def check(self, message: types.Message):
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.is_chat_admin()

with open("telegram.conf", 'r') as conf_f:
    token = conf_f.read().split("\n")[0].split(":", maxsplit=1)[1].strip()


    
bot = Bot(token)
dp = Dispatcher(bot, storage=MemoryStorage())
    
    
def __init__():
        global script_dir, conf_file, if_awaiting_repost_from_posting_channel, if_last_success
        script_dir = os.path.dirname(os.path.realpath(__file__))
        conf_file = os.path.join(script_dir, "telegram.conf")
        _load_conf_from_file(source=conf_file)
        
        logging.basicConfig(level=logging.INFO)

        if_awaiting_repost_from_posting_channel = False
        if_last_success = True

        #loop = asyncio.get_event_loop()
        #task = loop.create_task(_report_failed_messages())
        #loop.run_forever()
        
        executor.start_polling(dp, skip_updates=True)

#async def _report_failed_messages(timeout=30):
#        while True:
#            for id in config['admins_with_enabled_error_notifications']:
#                await bot.send_message(id, localizations["error_sending"])
#                if_last_success = True
#                await asyncio.sleep(timeout)
# Ifaces

@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message) -> None:
        """
        /start | help
        """
        #admins_id
        await message.reply(localizations["start"])


@dp.message_handler(commands=['reg'])
async def reg(message: types.Message) -> None:
        """
        /reg | /reg ID
        """
        global if_awaiting_repost_from_posting_channel
        message_splited = message.text.split()
        try:
            if len(message_splited) == 1:
                if_awaiting_repost_from_posting_channel = True
                await message.reply(localizations["reg_await"])
                return
            elif len(message_splited) == 2:
                _setup_given_channel_id(id=message_splited[1])
        except Exception as e:
            print("Registration failed")
            print(e.message)
        await message.reply(localizations["reg_falied"])
        return

@dp.message_handler(commands=['test'])
async def test(message: types.Message) -> None:
        """
        /test
        """
        text = " T e s t "
        try:
            await Bot.send_message(chat_id=config["channel_id"], text=text)
            if_last_success = True
        except Exception as e:
            print("Testing was unsuccesful")
            print(e.message)
            if_last_success = False

        return

#['animation', 'audio', 'video','photo','document','']))
@dp.message_handler(filters.MediaGroupFilter(is_media_group=True), content_types="photo")
@media_group_handler
async def album_handler(messages: list[types.Message]):
    full = None
    for message in messages:
        target = await bot.get_chat(config['channel_id'])
        yohoho_dict = PirateStation().canibalize_message(message=message, target= target.username, target_title=config["title"])
        if full is None:
            full = yohoho_dict
        else:
            if yohoho_dict.get("photo"):
                if full.get("photo"):
                    full["photo"].append(yohoho_dict["photo"][0])
                else:
                    full["photo"] = yohoho_dict["photo"]
            if yohoho_dict.get("video"):
                if full.get("video"):
                    full["video"].append(yohoho_dict["video"][0])
                else:
                    full["video"] = yohoho_dict["video"]           
    await _send_generic_message(message_args=full)

@dp.message_handler(filters.ForwardedMessageFilter(is_forwarded=True), content_types="any")
async def repost(message: types.Message):
        global if_awaiting_repost_from_posting_channel
        if if_awaiting_repost_from_posting_channel:
            try:
                _setup_given_channel_id(id=message.forward_from_chat, title=message.forward_from_chat.title)

                if_awaiting_repost_from_posting_channel = False
            except Exception as e:
                print("Reg Failed. Nothing Changed, go on. ")
                print(e.message)
                if_last_success = False
        else:
            # Well, well, well. No changes of text via API. Sucks to be us, doesn't it?
            # bot.copy_message(chat_id=config['channel_id'], from_chat_id=message.forward_from_chat, message_id=forward_from_message_id)
            # So, Jessie, let's cook             
            target = await bot.get_chat(config['channel_id'])
            yohoho_dict = PirateStation().canibalize_message(message=message, target= target.username, target_title=config["title"])
            await _send_generic_message(message_args=yohoho_dict)
# Service area

def _load_conf_from_file(source: str) -> None:
        global config, localizations
        config = {} 
        with open(source, 'r') as conf_file:
            for line in conf_file.read().split("\n"):
                name, value = [string.strip() for string in line.split(":", maxsplit=1)]
                value = [v.strip() for v in value.split(",")]
                value = value[0] if len(value) == 1 else value
                config[name] = value
        with open(os.path.join(script_dir, f"dict/{config['language']}.dict"), "r") as source :
            localizations = ast.literal_eval(source.read())
        return

def _write_conf_to_file(target: str) -> bool:
        lines = ""
        for name, value in config.items():
            lines += f'{name} : {",".join(value) if isinstance(value, list) else value}\n'
        try:
            with open(target, 'r+') as conf_file:
                conf_file.seek(0)
                conf_file.write(lines[:-1])
                conf_file.truncate()
        except Exception as e:
            print("Configuration change was unsuccesful.")
            print(e.message)
            raise
        return True
            
    # That doesn't work
def _if_valid_channel_id(channel_id: str|int) -> bool:
        #if isinstance(channel_id, str):
        #    try:
        #        channel_id = str(channel_id)
        #    except:
        #        return False
        return True

def _set_in_all_configurations(name: str, value: str) -> bool:
        global config
        config_backup = config
        try:
            config[name] = value
            _write_conf_to_file(target=conf_file)
        except Exception as e:
            config = config_backup
            print("Configuration change was unsuccesful. Configuration changes were reverted to previous state (nothing changed)")
            print(e.message)
            return False
        return True

def _setup_given_channel_id(id: str|int, title: str) -> bool:
        if not _if_valid_channel_id(id):
            raise 
        _set_in_all_configurations(name="channel_id", value=str(id.id))
        _set_in_all_configurations(name="title", value=id.title)

async def _send_generic_message(message_args: dict):
        parse_mode=types.ParseMode.MARKDOWN
#TODO: rewrite this monkey-brain code. It can be generalized and being used with audio, video, docs, photo as args
# Others should be whatever default. 
        if message_args['animation']:
            if len(message_args['animation']) < 2:
                return await bot.send_animation(
                    chat_id=config['channel_id'], 
                    animation=message_args['animation'],
                    caption=message_args['text'],
                    parse_mode=parse_mode)
            else:
                pass # no API, no multi-gifs
             
        elif message_args['audio']:
            if len(message_args['audio']) < 2:
                return await bot.send_audio(
                    chat_id=config['channel_id'], 
                    audio=message_args['audio'],
                    caption=message_args['text'],
                    parse_mode=parse_mode)
            else:
                media_gr = [types.InputMediaAudio(caption=message_args['text'] if first_in_pack else None, parse_mode=parse_mode, media=m) for m in message_args['audio']]
                first_in_pack = False
                return await bot.send_media_group(
                    chat_id=config['channel_id'], 
                    media=media_gr)

        elif message_args.get('photo'):
            if len(message_args['photo']) < 2:
                return await bot.send_photo(
                    chat_id=config['channel_id'], 
                    photo=message_args['photo'][0]['file_id'],
                    caption=message_args['text'],
                    parse_mode=parse_mode)
            else:
                t = 'photo'
                media_gr = types.MediaGroup()
                first_in_pack = True
                for m in message_args[t]:
                    media_gr.attach_photo(photo=types.InputMediaPhoto(caption=message_args['text'] if first_in_pack else None, parse_mode=parse_mode, media=m['file_id']), caption=message_args['text'])
                    first_in_pack = False
                return await bot.send_media_group(
                    chat_id=config['channel_id'], 
                    media=media_gr)
        
        elif message_args['video']:
            if not isinstance(message_args['video'], list):
                return await bot.send_video(
                    chat_id=config['channel_id'], 
                    video=message_args['video']['file_id'],
                    caption=message_args['text'],
                    parse_mode=parse_mode)
            else:
                t = 'video'
                media_gr = types.MediaGroup()
                first_in_pack = True
                for m in message_args[t]:
                    media_gr.attach_video(video=types.InputMediaVideo(caption=message_args['text'] if first_in_pack else None, parse_mode=parse_mode, media=m['file_id']), caption=message_args['text'])
                    first_in_pack = False
                return await bot.send_media_group(
                    chat_id=config['channel_id'], 
                    media=media_gr) 

        elif message_args['document']: #???
            if len(message_args['document']) < 2:
                return await bot.send_document(
                    chat_id=config['channel_id'], 
                    document=message_args['document'],
                    caption=message_args['text'],
                    parse_mode=parse_mode)
            else:
                media_gr = [types.InputMediaDocument(caption=message_args['text'], parse_mode=parse_mode, media=m) for m in message_args['document']]
                return await bot.send_media_group(
                    chat_id=config['channel_id'], 
                    media=media_gr)
                    
        return await bot.send_message(chat_id=config['channel_id'], text=message_args['text'], parse_mode=parse_mode)


class PirateStation:
    def __init__(self):
        self.message_dict = {"animation":None, "audio":None, "photo":None, "video":None, "document":None, "text":None}
        pass

    def canibalize_message(self, message: types.Message, target: str, target_title: str) -> dict:
        if message.animation:
            self._canibilize_animation_message(message)

        elif message.audio:
            self._canibilize_audio_message(message)

        elif message.photo:
            self._canibilize_photo_message(message)

        elif message.video:
            self._canibilize_video_message(message)
        
        elif message.document:
            self._canibilize_document_message(message) 
        try:
            text = message.text if message.text else message.md_text if message.md_text else message.caption
        except:
            text = ''    
        

        if message.forward_from:
            link_to_ch = f"[{target_title}](https://t.me/{target})"
            self.message_dict["text"] = f"""{link_to_ch}  
via DM  
[========]  
[========]
{text}"""
            
        else: 
            link_to_ch = f"[{target_title}](https://t.me/{target})"
            link_to_src = f"[{message.forward_from_chat.title}](https://t.me/{message.forward_from_chat.username}/{message.forward_from_message_id})"
            self.message_dict["text"] = f"""{link_to_ch}  
via: {link_to_src}  
[========]  
[========]       
{text}"""

        return self.message_dict
        

    def _canibilize_animation_message(self, message: types.Message) ->None:
        self.message_dict["animation"] = message.animation

    def _canibilize_audio_message(self, message: types.Message)->None:
        self.message_dict["audio"] = message.audio

    def _canibilize_photo_message(self, message: types.Message)->None:
        photos = message.photo
        self.message_dict["photo"] = [photos[-1],]
        #if not message.media_group_id:
        #    self.message_dict["photo"] = [photos[1],]
        #else:
        #    self.message_dict["photo"] = photos

    def _canibilize_video_message(self, message: types.Message)->None:
        self.message_dict["video"] = message.video

    def _canibilize_document_message(self, message: types.Message)->None:
        self.message_dict["document"] = message.document

__init__()

    

        
        
    

