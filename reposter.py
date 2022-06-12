#!/bin/python3.10
from email.mime import message
import logging
import os
import asyncio
#TODO: stats
#TODO: enable/disable source parsing: VK, TWitter, etc. Account-based or direct posting? RSS?
from aiogram import Bot, Dispatcher, executor, types



# copy_message

class Reposter:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.conf_file = os.path.join(self.script_dir, "telegram.conf")
        self._load_conf_from_file(source=self.conf_file)
        
        logging.basicConfig(level=logging.INFO)
        self.bot = Bot(token=API_TOKEN)
        self.dp = Dispatcher(bot)

        self.if_awaiting_repost_from_posting_channel = False
        self.if_last_success = True

        loop = asyncio.get_event_loop()
        task = loop.create_task(self._report_failed_messages())
        loop.run_forever(task)

    async def _report_failed_messages(self, timeout=30):
        while True:
            for id in self.config['admins_with_enabled_error_notifications']:
                await self.bot.send_message(id, self.localizations["error_sending"])
                self.if_last_success = True
                await asyncio.sleep(timeout)
# Ifaces

    @dp.message_handler(commands=['start', 'help'])
    async def start(self, message: types.Message) -> None:
        """
        /start | help
        """
        self.admins_id
        await message.reply(self.localizations["start"])


    @dp.message_handler(commands=['reg'])
    async def reg(self, message: types.Message) -> None:
        """
        /reg | /reg ID
        """
        message_splited = message.text.split()
        try:
            if message_splited.length == 1:
                self.if_awaiting_repost_from_posting_channel = True
                await message.reply(self.localizations["reg_await"])
                return
            elif message_splited.length == 2:
                self._setup_given_channel_id(id=message_splited[1])
        except Exception as e:
            print("Registration failed")
            print(e.message)
        await message.reply(self.localizations["reg_falied"])
        return

    @dp.message_handler(commands=['test'])
    async def test(self, message: types.Message) -> None:
        """
        /test
        """
        text = " T e s t "
        try:
            await Bot.send_message(chat_id=self.config["channel_id"], text=text)
            self.if_last_success = True
        except Exception as e:
            print("Testing was unsuccesful")
            print(e.message)
            self.if_last_success = False

        return

    @dp.message_handler(custom_filters=[Dispatcher.filters.ForwardedMessageFilter(is_forwarded=True)])
    async def repost(self, message: types.Message):
        if self.if_awaiting_repost_from_posting_channel:
            try:
                self._setup_given_channel_id(id=message.forward_from_chat, title=message.forward_from_chat.title)
                self.if_awaiting_repost_from_posting_channel = False
            except Exception as e:
                print("Reg Failed. Nothing Changed, go on. ")
                print(e.message)
                self.if_last_success = False
        else:
            # Well, well, well. No changes of text via API. Sucks to be us, doesn't it?
            # self.bot.copy_message(chat_id=self.config['channel_id'], from_chat_id=message.forward_from_chat, message_id=forward_from_message_id)
            # So, Jessie, let's cook             
            yohoho_dict = PirateStation().canibalize_message(message=message, target=self.config['channel_id'], target_title=self.config["title"])
            self._send_generic_message(message_args=yohoho_dict)

# Service area

    def _load_conf_from_file(self, source: str) -> None:
        self.config = {}
        with open(source, 'r') as conf_file:
            for line in conf_file.read():
                name, value = [string.strip() for string in line.split(":")]
                value = [v.strip() for v in value.split(",")]
                self.config[name] = value
        with open(os.path.join(self.script_dir, f"{self.config['language']}.conf"), "r") as source :
            self.localizations = source.read()
        return

    def _write_conf_to_file(self, target: str) -> bool:
        lines = ""
        for name, value in self.config.items():
            lines += '\n'.join(f'{name} : {",".join(value)}')
        try:
            with open(target, 'r+') as conf_file:
                conf_file.seek(0)
                conf_file.write(lines)
                conf_file.truncate()
        except Exception as e:
            print("Configuration change was unsuccesful.")
            print(e.message)
            raise
        return True
            
    # That doesn't work
    def _if_valid_channel_id(self, channel_id: str|int) -> bool:
        #if isinstance(channel_id, str):
        #    try:
        #        channel_id = str(channel_id)
        #    except:
        #        return False
        return True

    def _set_in_all_configurations(self, name: str, value: str) -> bool:
        config_backup = self.config
        try:
            self.config[name] = value
            self._write_conf_to_file(target=self.conf_file)
        except Exception as e:
            self.config = config_backup
            print("Configuration change was unsuccesful. Configuration changes were reverted to previous state (nothing changed)")
            print(e.message)
            return False
        return True

    def _setup_given_channel_id(self, id: str|int, title: str) -> bool:
        if not self._if_valid_channel_id(id):
            raise 
        self._set_in_all_configurations(name="channel_id", value=id)
        self._set_in_all_configurations(name="title", value=title)

    async def _send_generic_message(self, message_args: dict):
        parse_mode=types.ParseMode.Markdown
#TODO: rewrite this monkey-brain code. It can be generalized and being used with audio, video, docs, photo as args
# Others should be whatever default. 
        if message_args.animation:
            if message_args.animation.length < 2:
                return await self.bot.send_animation(
                    chat_id=self.config['channel_id'], 
                    animation=message_args['animation'],
                    caption=message_args['text'],
                    parse_mode=parse_mode)
            else:
                pass # no API, no multi-gifs
             
        elif message_args.audio:
            if message_args.audio.length < 2:
                return await self.bot.send_animation(
                    chat_id=self.config['channel_id'], 
                    audio=message_args['audio'],
                    caption=message_args['text'],
                    parse_mode=parse_mode)
            else:
                media_gr = [types.InputMediaAudio(caption=message_args['text'], parse_mode=parse_mode, media=m) for m in message_args['audio']]
                return await self.bot.send_animation(
                    chat_id=self.config['channel_id'], 
                    media=media_gr)

        elif message_args.photo:
            if message_args.photo.length < 2:
                return await self.bot.send_animation(
                    chat_id=self.config['channel_id'], 
                    photo=message_args['photo'],
                    caption=message_args['text'],
                    parse_mode=parse_mode)
            else:
                media_gr = [types.InputMediaPhoto(caption=message_args['text'], parse_mode=parse_mode, media=m) for m in message_args['photo']]
                return await self.bot.send_animation(
                    chat_id=self.config['channel_id'], 
                    media=media_gr)
        
        elif message_args.video:
            if message_args.video.length < 2:
                return await self.bot.send_animation(
                    chat_id=self.config['channel_id'], 
                    photo=message_args['video'],
                    caption=message_args['text'],
                    parse_mode=parse_mode)
            else:
                media_gr = [types.InputMediaVideo(caption=message_args['text'], parse_mode=parse_mode, media=m) for m in message_args['video']]
                return await self.bot.send_animation(
                    chat_id=self.config['channel_id'], 
                    media=media_gr) 

        elif message_args.document:
            if message_args.photo.length < 2:
                return await self.bot.send_animation(
                    chat_id=self.config['channel_id'], 
                    photo=message_args['document'],
                    caption=message_args['text'],
                    parse_mode=parse_mode)
            else:
                media_gr = [types.InputMediaDocument(caption=message_args['text'], parse_mode=parse_mode, media=m) for m in message_args['document']]
                return await self.bot.send_animation(
                    chat_id=self.config['channel_id'], 
                    media=media_gr)
                    
        return await self.bot.send_message(chat_id=self.config['channel_id'], text=message_args['text'], parse_mode=parse_mode)


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
        
        text = message.text if hasattr(message.text) else message.caption

        if message.forward_from:
            link_to_ch = f"[{target_title}](https://t.me/{target}&text=)"
            self.message_dict["text"] = f"""{link_to_ch}  
via DM  
[========]  
[========]
{text}"""
            
        else: 
            link_to_ch = f"[{target_title}](https://t.me/{target}&text=)"
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
        self.message_dict["photos"] = message.photo

    def _canibilize_video_message(self, message: types.Message)->None:
        self.message_dict["video"] = message.video

    def _canibilize_document_message(self, message: types.Message)->None:
        self.message_dict["document"] = message.document


    
        



    

        
        
    

