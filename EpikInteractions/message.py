from .sticker import *
from urllib.parse import quote
from .threads import *
from .reaction import Reaction
from typing import (
    Optional,
    Union,
    List,
    Any
)
from .application import Application
from .embed import Embed
from .user import *
from .mentioned import *
from .member import GuildMember
from .components import *
from logging import getLogger

logger = getLogger(__name__)


class MessageInteraction:
    def __init__(self, client, data: dict):
        self.id: str = data.get("id")
        self.type: int = data.get("type")
        self.name: str = data.get("name")
        self.user: User = User(client, data.get("user"))
        self.member: Optional[GuildMember] = GuildMember(client, data.get("member")) if data.get("member") else None
        self.user: User = User(client, data.get("user"))


class Message:
    """Represents a Discord message.
    
    Attributes
    ----------
    id : str
        The message ID.
    channel_id : str
        The channel ID the message was sent in.
    author : :class:`User`
        The author of the message 
    guild_id: str
        The Guild ID the message was sent in"""
    def __init__(self, client, data: dict):
        self.client = client
        self.id: str = data.get("id")
        self.channel_id: str = data.get("channel_id")
        self.guild_id: Optional[str] = data.get("guild_id")
        self.webhook_id: Optional[str] = data.get("webhook_id")
        self.author: Optional[Union[WebhookUser, User]] = WebhookUser(data.get("author")) if data.get("webhook_id") else User(client, data.get("author"))
        self.member: GuildMember = GuildMember(client, data.get("member")) if data.get("member") else None
        # I forgot Message Intents are gonna stop this.
        self.content: Optional[str] = data.get("content")
        self.timestamp: str = data.get("timestamp")
        self.edited_timestamp: Optional[str] = data.get("edited_timestamp")
        self.tts: bool = data.get("tts")
        self.mention_everyone: bool = data.get("mention_everyone")
        self.mentions: Optional[List[MentionedUser]] = [MentionedUser(client, mention) for mention in data.get("mentions", [])]
        self.mention_roles: Optional[List[int]] = data.get("mention_roles")
        self.mention_channels: Optional[List[MentionedChannel]] = [MentionedChannel(channel) for channel in data.get("mention_channels", [])]
        self.embeds: Optional[List[Embed]] = [Embed(**embed) for embed in data.get("embeds", [])]
        self.reactions: Optional[List[Reaction]] = [Reaction(reaction) for reaction in data.get("reactions", [])]
        self.nonce: Optional[Union[int, str]] = data.get("nonce")
        self.pinned: bool = data.get("pinned")
        self.type: int = data.get("type")
        self.activity: Optional[MessageActivity] = MessageActivity(
            data.get("activity")) if data.get("activity") else None
        # Despite there being a PartialApplication, Discord don't specify what attributes it has
        self.application: Application = Application(
            data.get("application")) if data.get("application") else None
        self.flags: int = data.get("flags")
        self.referenced_message: Optional[Message] = Message(client, data.get("referenced_message")) if data.get("referenced_message") else None
        self.interaction: Optional[MessageInteraction] = MessageInteraction(
            client, data.get("interaction")) if data.get("interaction") else None
        self.thread: Optional[Thread] = Thread(
            data.get("thread")) if data.get("thread") else None

        components: List[Any] = []
        if data.get("components"):
            for component in data.get("components"):
                if component.get("type") == 1:
                    components.append(MessageActionRow(component))
                elif component.get("type") == 2:
                    components.append(MessageButton(component))
                elif components.get("type") == 3:
                    components.append(MessageSelectMenu(component))
                elif components.get("type") == 4:
                    components.append(MessageTextInput(component))

        self.components: Optional[List[Union[MessageTextInput, MessageSelectMenu, MessageButton]]] = components
        self.stickers: Optional[List[StickerItem]] = [StickerItem(
            sticker) for sticker in data.get("stickers", [])] or None

    async def add_reaction(self, emoji: str):
        emoji = quote(emoji)
        logger.debug(f"Added a reaction to message ({self.id}).")
        response = await self.client.http.put(f"channels/{self.channel_id}/messages/{self.id}/reactions/{emoji}/@me")
        return await response.json()

    async def remove_reaction(self, emoji: str, user=None):
        emoji = quote(emoji)
        logger.debug(
            f"Removed reaction {emoji} from message ({self.id}) for user {user.username}.")
        if not user:
            response = await self.client.http.delete(f"channels/{self.channel_id}/messages/{self.id}/reactions/{emoji}/@me")
        else:
            response = await self.client.http.delete(f"channels/{self.channel_id}/messages/{self.id}/reactions/{emoji}/{user.id}")
        return await response.json()

    async def fetch_reactions(self, *, after, limit) -> List[Reaction]:
        logger.debug(f"Fetching reactions from message ({self.id}).")
        response = await self.client.http.get(f"channels/{self.channel_id}/messages/{self.id}/reactions?after={after}&limit={limit}")
        return await response.json()

    async def delete_all_reactions(self):
        logger.debug(f"Deleting all reactions from message ({self.id}).")
        response = await self.client.http.delete(f"channels/{self.channel_id}/messages/{self.id}/reactions")
        return await response.json()

    async def delete_reaction_for_emoji(self, emoji: str):
        logger.debug(
            f"Deleting a reaction from message ({self.id}) for emoji {emoji}.")
        emoji = quote(emoji)
        response = await self.client.http.delete(f"channels/{self.channel_id}/messages/{self.id}/reactions/{emoji}")
        return await response.json()

    async def edit(self, message_data: dict):
        logger.debug(
            f"Editing message {self.id} with message_data {message_data}.")
        response = await self.client.http.patch(f"channels/{self.channel_id}/messages/{self.id}", data=message_data)
        return await response.json()

    async def delete(self):
        logger.debug(f"Deleting message {self.id}.")
        response = await self.client.http.delete(f"channels/{self.channel_id}/messages/{self.id}")
        return await response.json()

    async def pin(self, *, reason: Optional[str]):
        headers = self.client.http.headers.copy()
        if reason:
            headers["X-Audit-Log-Reason"] = reason
            logger.debug(f"Pinning message {self.id} with reason {reason}.")
        else:
            logger.debug(f"Pinning message {self.id}.")
        response = await self.client.http.put(f"channels/{self.channel_id}/pins/{self.id}", headers=headers)
        return await response.json()

    async def unpin(self, *, reason: Optional[str]):
        headers = self.client.http.headers.copy()
        if reason:
            headers["X-Audit-Log-Reason"] = reason
            logger.debug(f"Unpinning message {self.id} with reason {reason}.")
        else:
            logger.debug(f"Unpinning message {self.id}.")
        response = await self.client.http.delete(f"channels/{self.channel_id}/pins/{self.id}", headers=headers)
        return await response.json()

    async def start_thread(self, name: str, auto_archive_duration: Optional[int], rate_limit_per_user: Optional[int]):
        logger.debug(
            f"Starting thread for message {self.id} with name {name}, auto archive duration {auto_archive_duration or None}, ratelimit per user {rate_limit_per_user or None}.")
        response = await self.client.http.post(f"channels/{self.channel_id}/messages/{self.id}/threads", data={"name": name, "auto_archive_duration": auto_archive_duration, "rate_limit_per_user": rate_limit_per_user})
        # Cache it
        self.client.guilds[self.guild_id].append(Thread(await response.json()))
        return Thread(await response.json())

    async def crosspost(self):
        logger.debug(f"Crossposting message {self.id}.")
        response = await self.client.http.post(f"channels/{self.channel_id}/messages/{self.id}/crosspost")
        return await response.json()