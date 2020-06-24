#!env /usr/bin/python

import traceback
# Extend this class to use common set of debug and request features for your script
from pprint import pprint

import LANforge.LFUtils
from LANforge.LFUtils import *


class LFCliBase:
    # do not use `super(LFCLiBase,self).__init__(self, host, port, _debug)
    # that is py2 era syntax and will force self into the host variable, making you
    # very confused.
    def __init__(self, _lfjson_host, _lfjson_port, _debug=False, _halt_on_error=False, _exit_on_error=False,
                 _exit_on_fail=False):
        self.fail_pref = "FAILED: "
        self.pass_pref = "PASSED: "
        self.lfclient_host = _lfjson_host
        self.lfclient_port = _lfjson_port
        self.debug = _debug
        self.haltOnError = _halt_on_error
        self.lfclient_url = "http://%s:%s" % (self.lfclient_host, self.lfclient_port)
        self.test_results = []
        self.exit_on_error = _exit_on_error
        self.exit_on_fail = _exit_on_fail
        # toggle using preexec_cli, preexec_method; the preexec_X parameters are useful
        # when you desire the lfclient to check for existance of entities to run commands on,
        # like when developing; you might toggle this with use_preexec = _debug
        # Otherwise, preexec methods use more processing time because they add an extra CLI call
        # into the queue, and inspect it -- typically nc_show_port
        self.use_preexec = False

    def clear_test_results(self):
        self.test_results.clear()

    def json_post(self, _req_url, _data):
        json_response = None
        try:
            lf_r = LFRequest.LFRequest(self.lfclient_url, _req_url, debug_=self.debug)
            if self.use_preexec == True:
                del _data['suppress_preexec_cli']
                del _data['suppress_preexec_method']
            else:
                _data['suppress_preexec_cli'] = True
                _data['suppress_preexec_method'] = True
            lf_r.addPostData(_data)
            if (self.debug):
                LANforge.LFUtils.debug_printer.pprint(_data)
            json_response = lf_r.jsonPost(show_error=self.debug, debug=self.debug)
        except Exception as x:
            if self.debug or self.haltOnError:
                print("jsonPost posted to %s" % _req_url)
                pprint(_data)
                print("Exception %s:" % x)
                traceback.print_exception(Exception, x, x.__traceback__, chain=True)
            if self.haltOnError:
                exit(1)

        return json_response

    def json_get(self, _req_url):
        if self.debug:
            print("URL: "+_req_url)
        json_response = None
        try:
            lf_r = LFRequest.LFRequest(self.lfclient_url, _req_url)
            json_response = lf_r.getAsJson(self.debug)
            #debug_printer.pprint(json_response)
            if (json_response is None) and self.debug:
                raise ValueError(json_response)
        except ValueError as ve:
            if self.debug or self.haltOnError:
                print("jsonGet asked for " + _req_url)
                print("Exception %s:" % ve)
                traceback.print_exception(ValueError, ve, ve.__traceback__, chain=True)
            if self.haltOnError:
                sys.exit(1)

        return json_response

    @staticmethod
    def response_list_to_map(json_list, key, debug_=False):
        reverse_map = {}
        if (json_list is None) or (len(json_list) < 1):
            if debug_:
                print("response_list_to_map: no json_list provided")
                raise ValueError("response_list_to_map: no json_list provided")
            return reverse_map

        json_interfaces = json_list
        if key in json_list:
            json_interfaces = json_list[key]

        for record in json_interfaces:
            if len(record.keys()) < 1:
                continue
            record_keys = record.keys()
            k2 = ""
            # we expect one key in record keys, but we can't expect [0] to be populated
            json_entry = None
            for k in record_keys:
                k2 = k
                json_entry = record[k]
            # skip uninitialized port records
            if k2.find("Unknown") >= 0:
                continue
            port_json = record[k2]
            reverse_map[k2] = json_entry

        return reverse_map


    def error(self, exception):
        # print("lfcli_base error: %s" % exception)
        pprint.pprint(exception)
        traceback.print_exception(Exception, exception, exception.__traceback__, chain=True)
        if self.haltOnError:
            print("halting on error")
            sys.exit(1)
        # else:
        #    print("continuing...")

    def check_connect(self):
        if self.debug:
            print("Checking for LANforge GUI connection: %s" % self.lfclient_url)
        response = self.json_get("/")
        duration = 0
        while (response is None) and (duration < 300):
            print("LANforge GUI connection not found sleeping 5 seconds, tried: %s" % self.lfclient_url)
            duration += 2
            time.sleep(2)
            response = self.json_get("")

        if duration >= 300:
            print("Could not connect to LANforge GUI")
            sys.exit(1)

    def get_result_list(self):
        return self.test_results

    def get_failed_result_list(self):
        fail_list = []
        for result in self.test_results:
            if not result.startswith("PASS"):
                fail_list.append(result)
        return fail_list

    def get_fail_message(self):
        fail_messages = self.get_failed_result_list()
        return "\n".join(fail_messages)

    def get_all_message(self):
        return "\n".join(self.test_results)

    def passes(self):
        pass_counter = 0
        fail_counter = 0
        for result in self.test_results:
            if result.startswith("PASS"):
                pass_counter += 1
            else:
                fail_counter += 1
        if (fail_counter == 0) and (pass_counter > 0):
            return True
        return False

    # use this inside the class to log a failure result
    def _fail(self, message, print_=False):
        self.test_results.append(self.fail_pref + message)
        if print_:
            print(self.fail_pref + message)
        if self.exit_on_error:
            sys.exit(1)

    # use this inside the class to log a pass result
    def _pass(self, message, print_=False):
        self.test_results.append(self.pass_pref + message)
        if print_:
            print(self.pass_pref + message)

# ~class
