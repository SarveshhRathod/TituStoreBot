import asyncio
import logging
from collections import OrderedDict
from typing import Dict, Union
from pyrogram import Client, utils, raw
from pyrogram.session import Session, Auth
from pyrogram.errors import AuthBytesInvalid
from pyrogram.file_id import FileId, FileType, ThumbnailSource

logger = logging.getLogger(__name__)

work_loads = {}
multi_clients = {}

# 2MB Chunk Size for higher throughput & fewer MTProto RPC calls
CHUNK_SIZE = 2 * 1024 * 1024

# RAM Byte Cache: LRU Cache storing max 50 chunks in memory (~100MB RAM buffer)
MAX_CACHE_ENTRIES = 50
_RAM_CHUNK_CACHE = OrderedDict()


def get_cached_chunk(cache_key: str):
    if cache_key in _RAM_CHUNK_CACHE:
        _RAM_CHUNK_CACHE.move_to_end(cache_key)
        return _RAM_CHUNK_CACHE[cache_key]
    return None


def set_cached_chunk(cache_key: str, data: bytes):
    if len(_RAM_CHUNK_CACHE) >= MAX_CACHE_ENTRIES:
        _RAM_CHUNK_CACHE.popitem(last=False)
    _RAM_CHUNK_CACHE[cache_key] = data


class ByteStreamer:
    def __init__(self, client: Client):
        self.clean_timer = 60 * 60  # 1 Hour TTL
        self.client: Client = client
        self.cached_file_ids: Dict[str, FileId] = {}
        asyncio.create_task(self.clean_cache())

    async def generate_media_session(self, client: Client, file_id: FileId) -> Session:
        media_session = client.media_sessions.get(file_id.dc_id, None)

        if media_session is None:
            if file_id.dc_id != await client.storage.dc_id():
                media_session = Session(
                    client,
                    file_id.dc_id,
                    await Auth(
                        client, file_id.dc_id, await client.storage.test_mode()
                    ).create(),
                    await client.storage.test_mode(),
                    is_media=True,
                )
                await media_session.start()

                for _ in range(6):
                    exported_auth = await client.invoke(
                        raw.functions.auth.ExportAuthorization(dc_id=file_id.dc_id)
                    )

                    try:
                        await media_session.invoke(
                            raw.functions.auth.ImportAuthorization(
                                id=exported_auth.id, bytes=exported_auth.bytes
                            )
                        )
                        break
                    except AuthBytesInvalid:
                        logger.debug(f"Invalid authorization bytes for DC {file_id.dc_id}")
                        continue
                else:
                    await media_session.stop()
                    raise AuthBytesInvalid
            else:
                media_session = Session(
                    client,
                    file_id.dc_id,
                    await client.storage.auth_key(),
                    await client.storage.test_mode(),
                    is_media=True,
                )
                await media_session.start()
            client.media_sessions[file_id.dc_id] = media_session
        return media_session

    @staticmethod
    async def get_location(file_id: FileId):
        file_type = file_id.file_type

        if file_type == FileType.CHAT_PHOTO:
            if file_id.chat_id > 0:
                peer = raw.types.InputPeerUser(
                    user_id=file_id.chat_id, access_hash=file_id.chat_access_hash
                )
            else:
                if file_id.chat_access_hash == 0:
                    peer = raw.types.InputPeerChat(chat_id=-file_id.chat_id)
                else:
                    peer = raw.types.InputPeerChannel(
                        channel_id=utils.get_channel_id(file_id.chat_id),
                        access_hash=file_id.chat_access_hash,
                    )

            location = raw.types.InputPeerPhotoFileLocation(
                peer=peer,
                volume_id=file_id.volume_id,
                local_id=file_id.local_id,
                big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG,
            )
        elif file_type == FileType.PHOTO:
            location = raw.types.InputPhotoFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )
        else:
            location = raw.types.InputDocumentFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )
        return location

    async def _fetch_getfile_raw(self, media_session, location, offset, chunk_size):
        try:
            r = await media_session.invoke(
                raw.functions.upload.GetFile(
                    location=location, offset=offset, limit=chunk_size
                ),
            )
            if isinstance(r, raw.types.upload.File):
                return r.bytes
        except Exception as e:
            logger.debug(f"MTProto GetFile fetch error: {e}")
        return b""

    async def yield_file(
        self,
        file_id: FileId,
        index: int,
        offset: int,
        first_part_cut: int,
        last_part_cut: int,
        part_count: int,
        chunk_size: int,
    ):
        client = self.client
        if index in work_loads:
            work_loads[index] += 1

        media_session = await self.generate_media_session(client, file_id)
        current_part = 1
        location = await self.get_location(file_id)
        unique_id = getattr(file_id, "unique_id", str(file_id.media_id))

        try:
            while True:
                cache_key = f"{unique_id}_{offset}_{chunk_size}"
                cached_data = get_cached_chunk(cache_key)

                if cached_data is not None:
                    chunk = cached_data
                else:
                    chunk = await self._fetch_getfile_raw(media_session, location, offset, chunk_size)
                    if chunk:
                        set_cached_chunk(cache_key, chunk)

                if not chunk:
                    break

                if part_count == 1:
                    yield chunk[first_part_cut:last_part_cut]
                elif current_part == 1:
                    yield chunk[first_part_cut:]
                elif current_part == part_count:
                    yield chunk[:last_part_cut]
                else:
                    yield chunk

                current_part += 1
                offset += chunk_size

                if current_part > part_count:
                    break

                # Prefetch next chunk in background task
                next_cache_key = f"{unique_id}_{offset}_{chunk_size}"
                if get_cached_chunk(next_cache_key) is None:
                    asyncio.create_task(self._prefetch_next(media_session, location, offset, chunk_size, next_cache_key))

        except (TimeoutError, AttributeError):
            pass
        finally:
            if index in work_loads:
                work_loads[index] -= 1

    async def _prefetch_next(self, media_session, location, offset, chunk_size, next_cache_key):
        chunk = await self._fetch_getfile_raw(media_session, location, offset, chunk_size)
        if chunk:
            set_cached_chunk(next_cache_key, chunk)

    async def clean_cache(self) -> None:
        while True:
            await asyncio.sleep(self.clean_timer)
            self.cached_file_ids.clear()
            logger.debug("Cleaned FileProperties Cache")
