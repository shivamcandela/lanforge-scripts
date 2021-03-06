#!/usr/bin/python3

##################################################################################
# Module contains functions to interact with CloudSDK using APIs
# Start by calling get_bearer to obtain bearer token, then other APIs can be used
#
# Used by Nightly_Sanity and Throughput_Test #####################################
##################################################################################

import base64
import urllib.request
from bs4 import BeautifulSoup
import ssl
import subprocess, os
from artifactory import ArtifactoryPath
import tarfile
import paramiko
from paramiko import SSHClient
from scp import SCPClient
import os
import pexpect
from pexpect import pxssh
import sys
import paramiko
from scp import SCPClient
import pprint
from pprint import pprint
from os import listdir
import re
import requests
import json
import testrail_api
import logging
import datetime
import time

user=os.getenv('CLOUDSDK_USER')
password=os.getenv('CLOUDSDK_PWD')

###Class for CloudSDK Interaction via RestAPI
class CloudSDK:
    def __init__(self):
        self.user = user

    def get_bearer(cloudSDK_url):
        cloud_login_url = cloudSDK_url+"/management/v1/oauth2/token"
        payload = '''
        {
        "userId": "'''+user+'''",
        "password": "'''+password+'''"
        }   
        '''
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            token_response = requests.request("POST", cloud_login_url, headers=headers, data=payload)
        except requests.exceptions.RequestException as e:
            raise SystemExit("Exiting Script! Cloud not get bearer token for reason:",e)
        token_data = token_response.json()
        bearer_token = token_data['access_token']
        return(bearer_token)

    def ap_firmware(customer_id,equipment_id, cloudSDK_url, bearer):
        equip_fw_url = cloudSDK_url+"/portal/status/forEquipment?customerId="+customer_id+"&equipmentId="+equipment_id
        payload = {}
        headers = {
            'Authorization': 'Bearer ' + bearer
        }
        status_response = requests.request("GET", equip_fw_url, headers=headers, data=payload)
        status_code = status_response.status_code
        if status_code is 200:
            status_data = status_response.json()
            #print(status_data)
            current_ap_fw = status_data[2]['details']['reportedSwVersion']
            return current_ap_fw
        else:
            return("ERROR")

    def CloudSDK_images(apModel, cloudSDK_url, bearer):
        getFW_url = cloudSDK_url+"/portal/firmware/version/byEquipmentType?equipmentType=AP&modelId=" + apModel
        payload = {}
        headers = {
            'Authorization': 'Bearer ' + bearer
        }
        response = requests.request("GET", getFW_url, headers=headers, data=payload)
        ap_fw_details = response.json()
        ###return ap_fw_details
        fwlist = []
        for version in ap_fw_details:
           fwlist.append(version.get('versionName'))
        return(fwlist)
        #fw_versionNames = ap_fw_details[0]['versionName']
        #return fw_versionNames

    def firwmare_upload(commit, apModel,latest_image,fw_url,cloudSDK_url,bearer):
        fw_upload_url = cloudSDK_url+"/portal/firmware/version"
        payload = "{\n  \"model_type\": \"FirmwareVersion\",\n  \"id\": 0,\n  \"equipmentType\": \"AP\",\n  \"modelId\": \""+apModel+"\",\n  \"versionName\": \""+latest_image+"\",\n  \"description\": \"\",\n  \"filename\": \""+fw_url+"\",\n  \"commit\": \""+commit+"\",\n  \"validationMethod\": \"MD5_CHECKSUM\",\n  \"validationCode\": \"19494befa87eb6bb90a64fd515634263\",\n  \"releaseDate\": 1596192028877,\n  \"createdTimestamp\": 0,\n  \"lastModifiedTimestamp\": 0\n}\n\n"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + bearer
        }

        response = requests.request("POST", fw_upload_url, headers=headers, data=payload)
        #print(response)
        upload_result = response.json()
        return(upload_result)

    def get_firmware_id(latest_ap_image, cloudSDK_url, bearer):
        #print(latest_ap_image)
        fw_id_url = cloudSDK_url+"/portal/firmware/version/byName?firmwareVersionName="+latest_ap_image

        payload = {}
        headers = {
            'Authorization': 'Bearer ' + bearer
        }
        response = requests.request("GET", fw_id_url, headers=headers, data=payload)
        fw_data = response.json()
        latest_fw_id = fw_data['id']
        return latest_fw_id

    def delete_firmware(fw_id, cloudSDK_url, bearer):
        url = cloudSDK_url + '/portal/firmware/version?firmwareVersionId=' + fw_id
        payload = {}
        headers = {
            'Authorization': 'Bearer ' + bearer
        }
        response = requests.request("DELETE", url, headers=headers, data=payload)
        return(response)

    def update_firmware(equipment_id, latest_firmware_id, cloudSDK_url, bearer):
        url = cloudSDK_url+"/portal/equipmentGateway/requestFirmwareUpdate?equipmentId="+equipment_id+"&firmwareVersionId="+latest_firmware_id

        payload = {}
        headers = {
            'Authorization': 'Bearer ' + bearer
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        #print(response.text)
        return response.json()

    def set_ap_profile(equipment_id, test_profile_id, cloudSDK_url, bearer):
        ###Get AP Info
        url = cloudSDK_url+"/portal/equipment?equipmentId="+equipment_id
        payload = {}
        headers = {
            'Authorization': 'Bearer ' + bearer
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        print(response)

        ###Add Lab Profile ID to Equipment
        equipment_info = response.json()
        #print(equipment_info)
        equipment_info["profileId"] = test_profile_id
        #print(equipment_info)

        ###Update AP Info with Required Profile ID
        url = cloudSDK_url+"/portal/equipment"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + bearer
        }

        response = requests.request("PUT", url, headers=headers, data=json.dumps(equipment_info))
        #print(response)

    def get_cloudsdk_version(cloudSDK_url, bearer):
        #print(latest_ap_image)
        url = cloudSDK_url+"/ping"

        payload = {}
        headers = {
            'Authorization': 'Bearer ' + bearer
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        cloud_sdk_version = response.json()
        return cloud_sdk_version

