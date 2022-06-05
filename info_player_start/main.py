import platform
import asyncio
from dotenv import load_dotenv as __load_dotenv
__load_dotenv()
from . import app


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy( asyncio.WindowsSelectorEventLoopPolicy() )
    asyncio.run( app.run() )
