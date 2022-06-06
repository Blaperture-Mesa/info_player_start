import pathlib
import asyncio
from mautrix.client import Client
from mautrix.types import (
    SyncToken
    , PaginationDirection
    , BaseRoomEvent
    , MessageEvent
    , RedactionEvent
    , TextMessageEventContent
    , RelatesTo
    , RelationType
)
from . import config, app



HISTORY_PATH = pathlib.Path( "bm.ips.history" )
if config.USE_JSON:
    HISTORY_PATH = pathlib.Path( "/tmp/bm/ips/history.json" )


def write_history (event: MessageEvent):
    config.datastore_write( HISTORY_PATH, {
        "event_id": event.event_id
    } )


def read_history ():
    msg = MessageEvent(
        None , None , None , None , None , None
    )
    try:
        msg.event_id = config.datastore_load( HISTORY_PATH )["event_id"]
    except:
        app.LOGGER.exception( "Failed to load history" )
    return msg


async def aiter_messages (client: Client, *args, **kwargs):
    await client.sync( full_state=True )
    token: SyncToken = None
    while (
        msg := await client.get_messages(
            *args
            , **kwargs
            , from_token=token
        )
    ).end != token:
        token = msg.end
        events: list[BaseRoomEvent] = msg.events
        for evt in events:
            yield evt


CLIENT_HISTORY_MSG_EVT = read_history()


async def get_history_id (room_id):
    global CLIENT_HISTORY_MSG_EVT
    oeid = old_evt_id = CLIENT_HISTORY_MSG_EVT.event_id or None
    if old_evt_id:
        async for evt in aiter_messages( app.CLIENT, room_id, PaginationDirection.BACKWARD ):
            if isinstance( evt, RedactionEvent ):
                if evt.redacts != old_evt_id:
                    continue
                old_evt_id = None
                break # deleted.
            elif isinstance( evt, MessageEvent ):
                msg_content = evt.content
                if not isinstance( msg_content, TextMessageEventContent ):
                    continue
                if evt.event_id != old_evt_id:
                    continue
                break # found.
        if not old_evt_id:
            app.LOGGER.warning( "update:Message %s is not found/deleted", oeid )
    return old_evt_id


async def edit_or_write_history (room_id, old_evt_id = None, **kwargs):
    global CLIENT_HISTORY_MSG_EVT
    new_evt_rt: RelatesTo = None
    if old_evt_id:
        new_evt_rt = RelatesTo( rel_type=RelationType.REPLACE, event_id=old_evt_id )
    new_evt_id = await app.CLIENT.send_notice( room_id, relates_to=new_evt_rt, **kwargs )
    await asyncio.sleep( 2 )
    i = 0
    async for evt in aiter_messages( app.CLIENT, room_id, PaginationDirection.BACKWARD ):
        i += 1
        if evt.event_id == new_evt_id:
            if not old_evt_id:
                CLIENT_HISTORY_MSG_EVT = evt
            break
        if i > 10:
            raise RuntimeError( "Message failed to send" )


@app.on( app.CustomEventType.POST_SHUTDOWN, False )
async def post_shutdown (_client: Client, _evt_type: app.CustomEventType):
    write_history( CLIENT_HISTORY_MSG_EVT )
