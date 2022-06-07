import logging
from typing import (
    Callable
    , ParamSpec
    , Concatenate
    , Awaitable
)
import asyncio
from collections import deque
from enum import Enum
from secrets import token_hex
from mautrix.client import Client
from mautrix.errors import MatrixRequestError
from mautrix.types import (
    LoginType
)
from . import config
from .datastore import BaseDatastore
__all__ = [
    "LOGGER"
    , "CLIENT"
    , "CustomEventType"
    , "on"
    , "run"
]



class CustomEventType (Enum):
    PRE_INIT = "pre_init"
    POST_INIT = "post_init"
    PRE_SYNC = "pre_sync"
    POST_SYNC = "post_sync"
    PRE_SHUTDOWN = "pre_shutdown"
    POST_SHUTDOWN = "post_shutdown"


_CLIENT_CUSTOM_EVENTS = {
    e.value: deque()
    for e
    in CustomEventType
}
_P = ParamSpec( '_P' )
_EVENT_FUNC = Callable[Concatenate[Client, CustomEventType, _P], Awaitable]
_LOGGED_IN = False


LOGGER = logging.getLogger()
CLIENT: Client = None
CLIENT_DATASTORE: BaseDatastore = None


async def __run_events (key: CustomEventType, *args, **kwargs):
    key_str = str( key.value )
    try:
        tasks = (
            (asyncio.create_task(x(*args, **kwargs)), wait_sync,)
            for x, wait_sync
            in _CLIENT_CUSTOM_EVENTS[key_str]
        )
        tasks = tuple(
            x
            for x,_
            in filter(lambda x: x[1], tasks)
        )
        if tasks:
            return await asyncio.gather(
                *tasks, return_exceptions=False
            )
    except Exception as exc:
        LOGGER.exception( "Event:%s:Exception occured", key.name, stack_info=True )
        return exc
    return tuple()


def on (evt_type: CustomEventType, wait_sync: bool=False) -> _EVENT_FUNC:
    def decorator (func: _EVENT_FUNC):
        events = _CLIENT_CUSTOM_EVENTS[str(evt_type.value)]
        def wrapper (*args, **kwargs):
            return func( CLIENT, evt_type, *args, **kwargs )
        events.append( (wrapper, wait_sync,) )
        LOGGER.debug( "Event:%s:Register:%s", evt_type.name, (func,wrapper,) )
        return wrapper
    return decorator


async def __login_by_token (user_id:str, device_id: str|None, token: str):
    CLIENT.mxid = user_id
    CLIENT.device_id = device_id
    CLIENT.api.token = token
    return (await CLIENT.whoami()).device_id == device_id


async def __init ():
    global CLIENT, _LOGGED_IN
    CLIENT = Client( base_url=config.BM_IPS_HOMESERVER )
    await __run_events( CustomEventType.PRE_INIT )

    if not CLIENT_DATASTORE:
        raise RuntimeError(
            f"Datastore is not configured"
            , type(CLIENT_DATASTORE).__name__
        )

    _LOGGED_IN = False
    creds = config.read_creds( CLIENT_DATASTORE )
    if creds:
        try:
            _LOGGED_IN = await __login_by_token( **creds )
            if not _LOGGED_IN:
                raise RuntimeError( "whoami.device_id is mismatched" )
        except (KeyError, ValueError, MatrixRequestError, RuntimeError) as exc:
            LOGGER.exception(
                "init:Failed to login with file: %s"
                , creds
            )

    if not _LOGGED_IN:
        user_id = config.BM_IPS_USERNAME
        device_id = config.BM_IPS_DEVICE_ID
        token = config.BM_IPS_TOKEN
        if token:
            if not device_id:
                raise ValueError( "Token is set but no device ID" )
            _LOGGED_IN = await __login_by_token( user_id, device_id, token )
        else:
            response = await CLIENT.login(
                identifier=user_id
                , device_id=device_id or None
                , device_name=f"PIPEDREAM-{token_hex(4).upper()}"
                , login_type=LoginType.PASSWORD
                , password=config.BM_IPS_PASSWORD
            )
            LOGGER.debug( "init:LoginResponse %s", response.json() )
            _LOGGED_IN = bool( response.access_token )
        if not _LOGGED_IN:
            raise RuntimeError( "Failed to login" )
        config.write_creds( CLIENT, CLIENT_DATASTORE )
    LOGGER.info( "init:Logged in: %s", (await CLIENT.whoami()).json() )
    await __run_events( CustomEventType.POST_INIT )
    return CLIENT


async def __sync ():
    try:
        await __run_events( CustomEventType.PRE_SYNC )
        tmp = CLIENT.start( None )
        await __run_events( CustomEventType.POST_SYNC )
        await tmp
    finally:
        CLIENT.stop()


async def run ():
    try:
        if await __init():
            LOGGER.info( "Started..." )
            await __sync()
    finally:
        await __run_events( CustomEventType.PRE_SHUTDOWN )
        await CLIENT.api.session.close()
        LOGGER.info( "Stopped..." )
        await __run_events( CustomEventType.POST_SHUTDOWN )


def set_datastore (datastore: BaseDatastore):
    global CLIENT_DATASTORE
    CLIENT_DATASTORE = datastore
    return CLIENT_DATASTORE
