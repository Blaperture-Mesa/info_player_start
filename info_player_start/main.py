import platform
import os
import asyncio
from secrets import token_hex
from mautrix.client import Client
from dotenv import load_dotenv as __load_dotenv
__load_dotenv()
from . import app, history


@app.on( app.CustomEventType.POST_SYNC )
async def update (client: Client, _evt_type: app.CustomEventType):
    try:
        room_id = os.environ.get( "BM_IPS_ROOM_STATS_ID" )
        await history.edit_or_write_history(
            room_id
            , await history.get_history_id( room_id )
            , text=token_hex( 16 )
        )
    finally:
        client.stop()


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy( asyncio.WindowsSelectorEventLoopPolicy() )
    asyncio.run( app.run() )
