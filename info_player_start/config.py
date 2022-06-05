USE_JSON = True
import logging
import json
from os import environ
from pathlib import Path
from mautrix.client import Client
if not USE_JSON:
    from pipedream.script_helpers import (steps, export)



BM_DEBUG = int( environ.get("BM_DEBUG", 0) )
BM_IPS_HCAPTCHA_TOKEN = environ.get( "BM_IPS_HCAPTCHA_TOKEN" )
BM_IPS_HOMESERVER = environ.get( "BM_IPS_HOMESERVER" )
BM_IPS_USERNAME = environ.get( "BM_IPS_USERNAME" )
BM_IPS_TOKEN = environ.get( "BM_IPS_TOKEN" )
BM_IPS_DEVICE_ID = environ.get( "BM_IPS_DEVICE_ID" )
BM_IPS_PASSWORD = environ.get( "BM_IPS_PASSWORD" )


CREDS_PATH = Path( "bm.ips.credentials" )
if USE_JSON:
    CREDS_PATH = Path( "/tmp/bm/ips/credentials.json" )


def datastore_write (outpath: Path, obj):
    if USE_JSON:
        outpath.parent.mkdir( parents=True, exist_ok=True )
        with outpath.open( "w" ) as fd:
            json.dump(
                obj
                , fd
                , separators=(',', ':')
            )
    else:
        key = str( outpath )
        export( key, obj )


def datastore_load (inpath: Path):
    if USE_JSON:
        try:
            with inpath.open( "r" ) as fd:
                return json.load( fd )
        except FileNotFoundError as exc:
            logging.debug( exc, exc_info=True )
        except (json.JSONDecodeError,):
            logging.critical( exc, exc_info=True )
    else:
        try:
            key = str(inpath).replace( '.', '_' )
            return steps[f"ds_get_{key}"]["$return_value"]
        except (KeyError):
            logging.critical( exc, exc_info=True )


def write_creds (client: Client):
    datastore_write( CREDS_PATH, {
        "user_id": client.mxid
        , "device_id": client.device_id
        , "token": client.api.token
    } )


def read_creds () -> dict | None:
    return datastore_load( CREDS_PATH )
