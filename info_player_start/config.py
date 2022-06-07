from os import environ
from pathlib import Path
from mautrix.client import Client
from .datastore import BaseDatastore



BM_DEBUG = int( environ.get("BM_DEBUG", 0) )
BM_IPS_HOMESERVER = environ.get( "BM_IPS_HOMESERVER" )
BM_IPS_USERNAME = environ.get( "BM_IPS_USERNAME" )
BM_IPS_TOKEN = environ.get( "BM_IPS_TOKEN" )
BM_IPS_DEVICE_ID = environ.get( "BM_IPS_DEVICE_ID" )
BM_IPS_PASSWORD = environ.get( "BM_IPS_PASSWORD" )


CREDS_PATH = Path( "bm/ips/credentials" )


def write_creds (client: Client, datastore: BaseDatastore):
    datastore.write( CREDS_PATH, {
        "user_id": client.mxid
        , "device_id": client.device_id
        , "token": client.api.token
    } )


def read_creds (datastore: BaseDatastore) -> dict | None:
    return datastore.read( CREDS_PATH )
