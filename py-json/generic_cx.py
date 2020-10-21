#!/usr/bin/env python3
import sys

if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit()

from LANforge.lfcli_base import LFCliBase

class GenericCx(LFCliBase):
    def __init__(self, lfclient_host, lfclient_port):
        super().__init__(lfclient_host, lfclient_port)
        self.lfclient_host = lfclient_host
        self.lfclient_port = lfclient_port

    def createGenEndp(self, alias=None, shelf=1, resource=1, port=None, type=None):
        if port is None:
            raise ValueError("createGenEndp: port required")
        if type is None:
            raise ValueError("createGenEndp: type required")

        data = {
            "alias": alias,
            "shelf": shelf,
            "resource": resource,
            "port": port,
            "type": type
        }
        super().json_post("cli-json/add_gen_endp", data)

    def setFlags(self, endpName, flagName, val):
        data = {
            "name": endpName,
            "flag": flagName,
            "val": val
        }
        super().json_post("cli-json/set_endp_flag", data)

    def setCmd(self, endpName, cmd):
        data = {
            "name": endpName,
            "command": cmd
        }
        super().json_post("cli-json/set_gen_cmd", data)
