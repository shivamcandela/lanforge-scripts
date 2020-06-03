#!/usr/bin/env python3
import re
import time
import pprint
from pprint import pprint
from LANforge import LFRequest
from LANforge import LFUtils
from LANforge import set_port
from LANforge import add_sta
from LANforge import lfcli_base
from LANforge.lfcli_base import LFCliBase

class Realm(LFCliBase):
    def __init__(self, lfclient_host="localhost", lfclient_port=8080, debug=False):
        super().__init__(lfclient_host, lfclient_port, debug, _halt_on_error=True)
        self.lfclient_url = f"http://{lfclient_host}:{lfclient_port}"
        super().check_connect()

    # Returns json response from webpage of all layer 3 cross connects
    def cx_list(self):
        response = super().json_get("/cx")
        return response

    # Returns list of all stations with "sta" in their name
    def station_list(self):
        sta_list = []
        response = super().json_get("/port/list?fields=_links,alias,device,port+type")
        if (response is None) or ("interfaces" not in response):
            print("station_list: incomplete response:")
            pprint(response)
            exit(1)
        for x in range(len(response['interfaces'])):
            for k,v in response['interfaces'][x].items():
                if ("sta" in v['device']) or ("wlan" in v['device']):
                    sta_list.append(response['interfaces'][x])

        return sta_list

    # Returns list of all VAPs with "vap" in their name
    def vap_list(self):
        sta_list = []
        response = super().json_get("/port/list?fields=_links,alias,device,port+type")
        for x in range(len(response['interfaces'])):
            for k,v in response['interfaces'][x].items():
                if "vap" in v['device']:
                    sta_list.append(response['interfaces'][x])

        return sta_list


    # Searches for ports that match a given pattern and returns a list of names
    def find_ports_like(self, pattern=""):
        device_name_list = []
        response = super().json_get("/port/list?fields=_links,alias,device,port+type")
        for x in range(len(response['interfaces'])):
            for k,v in response['interfaces'][x].items():
                if v['device'] != "NA":
                    device_name_list.append(v['device'])
        matched_list = []
        prefix = ""
        try:
            if pattern.find("+") > 0:
                match = re.search(r"^([^+]+)[+]$", pattern)
                if match.group(1):
                    #print("name:", port_name, " Group 1: ",match.group(1))
                    prefix = match.group(1)
                for port_name in device_name_list:
                    if port_name.find(prefix) == 0:
                        matched_list.append(port_name)

            elif pattern.find("*") > 0:
                match = re.search(r"^([^\*]+)[\*]$", pattern)
                if match.group(1):
                    prefix = match.group(1)
                    #print("group 1: ",prefix)
                for port_name in device_name_list:
                    if port_name.find(prefix) == 0:
                        matched_list.append(port_name)

            elif pattern.find("[") > 0:
                match = re.search(r"^([^\[]+)\[(\d+)\.\.(\d+)\]$", pattern)
                if match.group(0):
                    #print("[group1]: ", match.group(1))
                    #print("[group2]: ", match.group(2))
                    #print("[group3]: ", match.group(3))
                    prefix = match.group(1)
                    for port_name in device_name_list:
                        if port_name.find(prefix) == 0:
                            port_suf = port_name[len(prefix):]
                            if (port_suf >= match.group(2)) and (port_suf <= match.group(3)):
                                #print(f"{port_name}: suffix[{port_name}] between {match.group(2)}:{match.group(3)}")
                                matched_list.append(port_name) # wrong but better
        except ValueError as e:
            super().error(e)

        return matched_list

    def new_station_profile(self):
        station_prof = StationProfile(self.lfclient_url)
        return station_prof

    def new_cx_profile(self):
        cx_prof = CXProfile(self.lfclient_url)
        return cx_prof

class CXProfile:
    def __init__(self, lfclient_host, lfclient_port):
        self.lfclient_url = f"http://{lfclient_host}:{lfclient_port}/"
        self.post_data = []

    # Adds post data for a cross-connect between eth1 and specified list of ports, appends to array
    def add_ports(self, side, endp_type, ports=[]):
        side = side.upper()
        endp_side_a = {
        "alias":"",
        "shelf":1,
        "resource":1,
        "port":"",
        "type":endp_type,
        "min_rate":0,
        "max_rate":0,
        "min_pkt":-1,
        "max_pkt":0
        }

        endp_side_b = {
        "alias":"",
        "shelf":1,
        "resource":1,
        "port":"",
        "type":endp_type,
        "min_rate":0,
        "max_rate":0,
        "min_pkt":-1,
        "max_pkt":0
        }

        for port_name in ports:
            if side == "A":
                endp_side_a["alias"] = port_name+"CX-A"
                endp_side_a["port"] = port_name
                endp_side_b["alias"] = port_name+"CX-B"
                endp_side_b["port"] = "eth1"
            elif side == "B":
                endp_side_a["alias"] = port_name+"CX-A"
                endp_side_a["port"] = "eth1"
                endp_side_b["alias"] = port_name+"CX-B"
                endp_side_b["port"] = port_name

            lf_r = LFRequest.LFRequest(self.lfclient_url + "/cli-json/add_endp")
            lf_r.addPostData(endp_side_a)
            json_response = lf_r.jsonPost(True)
            lf_r.addPostData(endp_side_b)
            json_response = lf_r.jsonPost(True)
            #LFUtils.debug_printer.pprint(json_response)
            time.sleep(.5)


            data = {
            "alias":port_name+"CX",
            "test_mgr":"default_tm",
            "tx_endp":port_name + "CX-A",
            "rx_endp":port_name + "CX-B"
            }

            self.post_data.append(data)

    # Creates cross-connect for each port specified in the addPorts function
    def create(self, sleep_time=.5):
       for data in self.post_data:
           lf_r = LFRequest.LFRequest(self.lfclient_url + "/cli-json/add_cx")
           lf_r.addPostData(data)
           json_response = lf_r.jsonPost(True)
           #LFUtils.debug_printer.pprint(json_response)
           time.sleep(sleep_time)


# use the station profile to set the combination of features you want on your stations
# once this combination is configured, build the stations with the build(resource, radio, number) call
# build() calls will fail if the station already exists. Please survey and clean your resource
# before calling build()
#       survey = Realm.findStations(resource=1)
#       Realm.removeStations(survey)
#       profile = Realm.newStationProfile()
#       profile.set...
#       profile.build(resource, radio, 64)
#
class StationProfile:
    def __init__(self, lfclient_url, ssid="NA", ssid_pass="NA", security="open", start_id="", mode=0, up=True, dhcp=True):
        self.lfclient_url = lfclient_url
        self.ssid = ssid
        self.ssid_pass = ssid_pass
        self.mode = mode
        self.up = up
        self.dhcp = dhcp
        self.security = security
        self.COMMANDS = ["add_sta", "set_port"]
        self.desired_add_sta_flags = ["wpa2_enable", "80211u_enable", "create_admin_down"]
        self.add_sta_data = {
            "shelf": 1,
            "resource": 1,
            "radio": None,
            "sta_name": None,
            "ssid": None,
            "key": None,
            "mode": 0,
            "mac": "xx:xx:xx:xx:*:xx",
            "flags": 0, # (0x400 + 0x20000 + 0x1000000000)  # create admin down
        }
        self.desired_set_port_flags = ["down", "dhcp"]
        self.set_port_data = {
            "shelf": 1,
            "resource": 1,
            "port": None,
            "current_flags": 0,
            "interest": 0, #(0x2 + 0x4000 + 0x800000)  # current, dhcp, down,
        }

    def set_param(self, cli_name, param_name, param_val):
        # we have to check what the param name is
        if (cli_name is None) or (cli_name == ""):
            return
        if (param_name is None) or (param_name == ""):
            return
        if cli_name not in self.COMMANDS:
            print(f"Command name name [{cli_name}] not defined in {self.COMMANDS}")
            return
        if cli_name == "add_sta":
            if (param_name not in add_sta.add_sta_flags) or (param_name not in add_sta.add_sta_modes):
                print(f"Parameter name [{param_name}] not defined in add_sta.py")
                return
        elif cli_name == "set_port":
            if (param_name not in set_port.set_port_current_flags) or (param_name not in set_port.set_port_cmd_flags):
                print(f"Parameter name [{param_name}] not defined in set_port.py")
                return

    def add_named_flags(self, desired_list, command_ref):
        if desired_list is None:
            raise ValueError("addNamedFlags wants a list of desired flag names")
        if len(desired_list) < 1:
            print("addNamedFlags: empty desired list")
            return 0
        if (command_ref is None) or (len(command_ref) < 1):
            raise ValueError("addNamedFlags wants a maps of flag values")

        result = 0
        for name in desired_list:
            if (name not in command_ref):
                raise ValueError(f"flag {name} not in map")
            result += command_ref[name]

        return result

    # Checks for errors in initialization values and creates specified number of stations using init parameters
    def build(self, resource, radio, num_stations):
        # try:
        #     resource = resource_radio[0: resource_radio.index(".")]
        #     name = resource_radio[resource_radio.index(".") + 1:]
        #     if name.index(".") >= 0:
        #         radio_name = name[name.index(".")+1 : ]
        #     print(f"Building {num_stations} on radio {resource}.{radio_name}")
        # except ValueError as e:
        #     print(e)

        # create stations down, do set_port on them, then set stations up
        self.add_sta_data["flags"] = self.add_named_flags(self.desired_add_sta_flags, add_sta.add_sta_flags)
        self.add_sta_data["radio"] = radio
        self.add_sta_data["resource"] = resource
        lf_r = LFRequest.LFRequest(self.lfclient_url + "/cli-json/add_sta")
        for num in range(num_stations):
            self.add_sta_data["sta_name"] = f"sta{num:05}"
            lf_r.addPostData(self.add_sta_data)
            json_response = lf_r.jsonPost(True)
        print(f"created {num} stations")

#
