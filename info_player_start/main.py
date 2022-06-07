import platform
import asyncio
from mautrix.client import Client
from dotenv import load_dotenv as __load_dotenv
__load_dotenv()
from . import datastore, app



@app.on( app.CustomEventType.PRE_INIT, True )
async def update (_client: Client, _evt_type: app.CustomEventType):
    #app.set_datastore( datastore.JSONDatastore("/tmp/") )
    pass


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy( asyncio.WindowsSelectorEventLoopPolicy() )
    asyncio.run( app.run() )
