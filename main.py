#!/usr/local/bin/python3.12
import os
import ast
import logging
from dotenv import load_dotenv


from aiogram import Bot, Dispatcher, executor, types, filters
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_media_group import media_group_handler
from aiogram.filters import BoundFilter


from models.tg.model import TGChannel, Message

load_dotenv( dotenv_path = "conf/.env" )
token = os.env( "TOKEN" )
channel_id = os.env( "CHANNEL_ID" )
bot = Bot( token )
dp = Dispatcher( bot, storage=MemoryStorage() )
# Deprecated
with open( os.path.join( "control/tg/", f"dict/en.dict"), "r" ) as source :
    localizations = ast.literal_eval(source.read())


class MyFilter(BoundFilter):
    key = 'is_admin'

    def __init__( self, is_admin ):
        self.is_admin = is_admin

    async def check( self, message: types.Message ):
        member = await bot.get_chat_member( message.chat.id, message.from_user.id )
        return member.is_chat_admin()
    
def main():
        global script_dir, conf_file, if_awaiting_repost_from_posting_channel, if_last_success
        
        logging.basicConfig(level=logging.INFO)

        if_awaiting_repost_from_posting_channel = False 
        if_last_success = True

        executor.start_polling(dp, skip_updates=True)

@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message) -> None:
        """
        /start | help
        """
        #admins_id
        await message.reply(localizations["start"])

# Deprecated
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
    if not isinstance( messages, list ):
        messages = [ messages, ] 
    global channel_id
    tgapi_channel = await bot.get_chat( channel_id )
    target = TGChannel( tgapi_channel.title, tgapi_channel.username, channel_id )
    for message in messages:
        message = Message.from_aiogram( original_message = message, target_TGChannel = target )
        await message.send( bot )    

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
            if not isinstance( messages, list ):
                messages = [ messages, ] 
            global channel_id
            tgapi_channel = await bot.get_chat( channel_id )
            target = TGChannel( tgapi_channel.title, tgapi_channel.username, channel_id )
            for message in messages:
                message = Message.from_aiogram( original_message = message, target_TGChannel = target )
                await message.send( bot )  
# Service area
# deprecated
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
    
# deprecated
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
        
# deprecated    
    # That doesn't work
def _if_valid_channel_id(channel_id: str|int) -> bool:
        #if isinstance(channel_id, str):
        #    try:
        #        channel_id = str(channel_id)
        #    except:
        #        return False
        return True
    
# deprecated
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
    
# deprecated
def _setup_given_channel_id(id: str|int, title: str) -> bool:
        if not _if_valid_channel_id(id):
            raise 
        _set_in_all_configurations(name="channel_id", value=str(id.id))
        _set_in_all_configurations(name="title", value=id.title)