import logging
import json
from typing import Any
from abc import abstractmethod
from pathlib import Path, PurePath, PureWindowsPath
from pipedream.script_helpers import (steps, export)



class BaseDatastore ():
    def format_path (self, path: PurePath) -> Path:
        return Path( path )

    @abstractmethod
    def read (self, inpath: Path) -> Any|None:
        pass

    @abstractmethod
    def write (self, outpath: Path, obj):
        pass


class FileDatastore (BaseDatastore):
    def __init__ (self, base: Path) -> None:
        super().__init__()
        self.base: Path = Path( base )

    def format_path (self, path: PurePath) -> Path:
        return (self.base / super().format_path(path))


class JSONDatastore (FileDatastore):
    def format_path (self, path: PurePath) -> Path:
        path = super().format_path( path ).with_suffix( ".json" )
        return path

    def read (self, inpath: Path) -> Any|None:
        inpath = self.format_path( inpath )
        try:
            with inpath.open( "r" ) as fd:
                return json.load( fd )
        except FileNotFoundError as exc:
            logging.debug( exc, exc_info=True )
        except (json.JSONDecodeError,):
            logging.critical( exc, exc_info=True )
        return None

    def write (self, outpath: Path, obj) -> None:
        outpath = self.format_path( outpath )
        outpath.parent.mkdir( parents=True, exist_ok=True )
        with outpath.open( "w" ) as fd:
            json.dump(
                obj
                , fd
                , separators=(',', ':')
            )


class PipedreamDatastore (BaseDatastore):
    def format_path (self, path: PurePath) -> Path:
        pstr = str( super().format_path(path) )
        if isinstance( path, PureWindowsPath ):
            pstr = pstr.replace( '\\', '.' )
        else:
            pstr = pstr.replace( '/', '.' )
        return Path( pstr )

    @abstractmethod
    def read (self, inpath: Path) -> Any|None:
        try:
            key = str( self.format_path(inpath) )
            key = f"ds_get_{key}"
            return steps[key]["$return_value"]
        except (KeyError) as exc:
            logging.critical( exc, exc_info=True )
        return None

    @abstractmethod
    def write (self, outpath: Path, obj):
        key = str( self.format_path(outpath) )
        key = f"ds_set_{key}"
        export( key, obj )
