from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable
from aiogram.types import MediaGroup, ParseMode
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import InputMediaAudio, InputMediaDocument, InputMediaAnimation, InputMediaPhoto, InputMediaVideo
from aiogram.types import Message as aigMessage
from aiogram import Bot

@dataclass
class Source( ABC ):
    pass

@dataclass
class TGAuthor( Source ):
    pass

@dataclass
class TGChannel( TGAuthor ):
   title: str
   link: str
   idx: str
   
@dataclass
class TGUser( TGAuthor ):
    pass

@dataclass
class Message( ABC ):
    origin: TGChannel|None = None
    origin_msg_id: int|None = None
    target: TGChannel|None = None
    contnet: dict = {}
    
    # content_presence_table
    
    @abstractmethod
    @staticmethod
    def add_content_from_message( original_message: aigMessage, target_message: 'Message'  ):
        raise NotImplemented
    
    def _setup_signature( self ):
        link_to_ch = f"[{ self.target.title }](https://t.me/{ self.target.link })"
        if self.origin is TGChannel:
            link_to_src = f"[{ self.origin.title }](https://t.me/{ 
                ( self.origin.link + '/' + self.origin_msg_id )
            }"
        else:
            link_to_src = "DM"
        self.contnet[ "text" ] = link_to_ch + "\n" \
                                 + f"via: {link_to_src}\n" \
                                 + "[========]\n" \
                                 + "[========]\n" \
                                 + self.contnet[ "text" ]


    @staticmethod
    def from_aiogram( original_message: aigMessage = None, original_messages: list[ aigMessage ] = None, target_TGChannel: TGChannel = None ):
        if original_message and original_messages:
            raise
        if original_message:
            original_messages = [ original_message, ]
            
        target_message = Message()
        target_message.target = target_TGChannel
        target_message.origin = TGChannel( 
            title=original_message.forward_from_chat.title,
            link=original_message.forward_from_chat.TGUsername
        )
        
        for original_message in original_messages:
            Message.parse_one_message( original_message, target_message )
        
        target_message._setup_signature()
        return target_message
   
    def send( self, engine: Bot ):
        media_elements_counter = 0
        
        for tool, if_present in self.content_presence_table.items():
            if if_present:
                media_elements_counter += tool.calculate_quantity_contents( self )
            if media_elements_counter > 2:
                break
            
        if media_elements_counter > 2: 
            self._single_send( engine )
            return
        
        self._send_mediagroup( engine )
                
    @classmethod
    def parse_one_message( cls, original_message: aigMessage, target_message: 'Message' ) -> None:
        contains = lambda attribute: getattr( original_message, attribute, None ) != None
        content_presence_table: dict[ Message, bool ] = {
                MessageAnimationTool: contains( "animation" ),
                MessageAudioTool: contains( "audio" ),
                MessagePhotoTool: contains( "photo" ),
                MessageVideoTool: contains( "video" ),
                MessageDocumentTool: contains( "document" ),
                MessageTextTool: True
        }
        
        for tool, if_present in content_presence_table.items():
            if not if_present:
                continue
            tool.add_content_from_message( original_message, target_message ) 
            
        for key, value in content_presence_table.items():
            target_message.content_presence_table[ key ] = target_message.content_presence_table[ key ] or value


    async def _single_send( self, engine: Bot ) -> None:
        kwargs = { 
            "chat_id": self.target.idx, 
            "caption": self.contnet[ "text" ],
            "parse_mode": ParseMode.MARKDOWN #TODO: ENV
        }
        send: Callable
        for tool, if_present in self.content_presence_table.items():
            if not if_present:
                continue
            send = getattr( engine, tool.get_send_function() )
            kwargs += tool.get_content_for_message_type( self )
            break
        await send( **kwargs )
        
    async def _send_mediagroup( self, engine: Bot ) -> None:
        media_group = MediaGroupBuilder( caption = self.contnet[ "text" ] )
        kwargs = { 
            "chat_id": self.target.idx, 
            "caption": self.contnet[ "text" ],
            "parse_mode": ParseMode.MARKDOWN #TODO: ENV
        }
        for tool, if_present in self.content_presence_table.items():
            if not if_present:
                continue
            tool.add_to_mediagroup( self, media_group )
        kwargs[ "media" ] = media_group.build()
        await engine.send_media_group( **kwargs )
            
        
class MessageTool( ABC ):
    tool_type: str = ""
    
    @classmethod
    def add_content_from_message( cls, original_message: aigMessage, target_message: Message ) -> None:
        target_message.contnet[ cls.tool_type ] = getattr( original_message, cls.tool_type )
        
    @classmethod
    def calculate_quantity_contents( cls, target_message: Message ) -> int:
        return len( target_message.contnet[ cls.tool_type ] )
    
    @classmethod
    def get_content_for_message_type( cls, target_message: Message ) -> dict[ str, str ]:
        return { cls.tool_type: target_message.contnet[ cls.tool_type ] }
    
    @classmethod
    def add_to_mediagroup( cls, target_message: Message, target_mediagroup: MediaGroup ) -> None:
        pass

    @staticmethod
    def get_send_function() -> str:
        return 'send_message'

class MessageAnimationTool( MessageTool ):
    tool_type: str = "animation"
    
    @staticmethod
    def get_send_function() -> str:
        return 'send_animation'
    
    @classmethod
    def add_to_mediagroup( cls, target_message: Message, target_mediagroup: MediaGroup ) -> None:
        pass # NotImplemented by tg

class MessageAudioTool( MessageTool ):
    tool_type: str = "audio"
    
    @staticmethod
    def get_send_function() -> str:
        return 'send_audio'
    
    @classmethod
    def add_to_mediagroup( cls, target_message: Message, target_mediagroup: MediaGroupBuilder ) -> None:
        for content in target_message.content[ cls.tool_type ]:
            target_mediagroup.add_audio( content )
                 
class MessagePhotoTool( MessageTool ):
    tool_type: str = "photo"
    
    @classmethod
    def add_content_from_message( cls, original_message: aigMessage, target_message: Message ) -> None:
        target_message.contnet[ cls.tool_type ] = [ original_message.photo[-1], ]
        
    @classmethod
    def get_content_for_message_type( cls, target_message: Message ) -> dict[ str, str ]:
        return { cls.tool_type: target_message.contnet[ cls.tool_type ][ 0 ][ "file_id" ] }
    
    @classmethod
    def add_to_mediagroup( cls, target_message: Message, target_mediagroup: MediaGroupBuilder ) -> None:
        for content in target_message.content[ cls.tool_type ]:
            target_mediagroup.add( 
                type = cls.tool_type,
                media = content[ "file_id" ] 
            )
            
    @staticmethod
    def get_send_function() -> str:
        return 'send_photo'
    
class MessageVideoTool( MessageTool ):
    tool_type: str = "video"
    
    @classmethod
    def get_content_for_message_type( cls, target_message: Message ) -> dict[ str, str ]:
        return { cls.tool_type: target_message.contnet[ cls.tool_type ][ "file_id" ] }
    
    @classmethod
    def add_to_mediagroup( cls, target_message: Message, target_mediagroup: MediaGroupBuilder ) -> None:
        for content in target_message.content[ cls.tool_type ]:
            target_mediagroup.add( 
                type = cls.tool_type,
                media = content[ "file_id" ]
            )

    @staticmethod
    def get_send_function() -> str:
        return 'send_video'
    
class MessageDocumentTool( MessageTool ):
    tool_type: str = "document"
    
    @classmethod
    def get_content_for_message_type( cls, target_message: Message ) -> dict[ str, str ]:
        return { cls.tool_type: target_message.contnet[ cls.tool_type ] }
    
    @classmethod
    def add_to_mediagroup( cls, target_message: Message, target_mediagroup: MediaGroupBuilder ) -> None:
        for content in target_message.content[ cls.tool_type ]:
            target_mediagroup.add( 
                type = cls.tool_type,
                media = content
            )
    @staticmethod
    def get_send_function() -> str:
        return 'send_document'
    
class MessageTextTool( MessageTool ):
    @classmethod
    def add_content_from_message( cls, original_message: aigMessage, target_message: Message ) -> None:
        text: str
        for attrib in ( "text", "md_text", "caption" ) :
            text = getattr( original_message, attrib, None )
            if text != None:
                break
        else:
            text = ""            
        target_message.contnet[ cls.tool_type ] = text
        
    @classmethod
    def calculate_quantity_contents( cls, target_message: Message ):
        return 1
