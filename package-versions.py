import requests
from requests.auth import HTTPDigestAuth
import xml.etree.ElementTree as ET
from prettytable import PrettyTable
from datetime import datetime

fws_username = ""
fws_password = ""
dev1_username = ""
dev1_password = ""
dev2_username = ""
dev2_password = ""
fws_url = "fws/url/di/services/"
dev1_url = "dev1/url/di/services/"
dev2_url = "dev2/url/di/services/"
package_search = ""
search_prompt = "For which package would you like to pull back batch execution records? Please check your spelling carefully.  "


class Package:
    def __init__(self, name, version, deployed_date):
        self.name = name
        self.version = version
        self.deployedDate = deployed_date


class BatchJob:
    def __init__(self, package_name, version, service_return_code, start_time, end_time):
        self.package_name = package_name
        self.version = version
        self.service_return_code = service_return_code
        self.start_time = start_time
        self.end_time = end_time


def get_all_packages_and_print_table(api_url, env_name, user, password):
    url = api_url

    response = requests.get(url, auth=HTTPDigestAuth(user, password))

    if response.status_code != 200:
        print("Your request for {0} was denied. Status code {1} Please check your username/password.".format(env_name, response.status_code))
        return

    root = ET.fromstring(response.content)

    info_list = []

    for package in root.findall('./package'):
        this_package = Package
        for name in package.findall('./name'):
            this_package.name = name.text
        for version in package.findall('./version'):
            this_package.version = version.text
        for date in package.findall('./deployDate'):
            this_package.deployedDate = date.text
        pack_obj = Package(this_package.name, this_package.version, this_package.deployedDate)
        info_list.append(pack_obj)

    info_list.sort(key=lambda x: (x.name, x.deployedDate))
    headers = ["Name", "Version", "Deployed Date"]

    table = PrettyTable(headers)
    for row in range(len(info_list)):
        table.add_row([info_list[row].name, info_list[row].version, info_list[row].deployedDate])

    print(env_name)
    print(table)


def pull_batch_info(env_name, url_base, package_to_search, username, password):
    print("Processing Results. This may take a while.")
    # package_to_search = "BBVA_Maintenance_IB"
    # term_to_search = "BBVA_USCL_Letter_OB"
    response = requests.get(url_base + "batch/jobs", auth=HTTPDigestAuth(username, password))

    if response.status_code != 200:
        print("Your request for {0} was denied. Status code {1} Please check your username/password.".format(env_name, response.status_code))
        return

    root = ET.fromstring(response.content)
    batch_job_list = []
    for job in root.findall('./job'):
        batch_job_list.append(job.attrib['{http://www.w3.org/1999/xlink}href'])
    job_results_to_search = []
    for route in range(50):
        this_job = BatchJob
        response = requests.get(batch_job_list[route], auth=HTTPDigestAuth(username, password))
        this_job.package_name = response.json()['job']['runtimeConfig']['packageName']
        this_job.version = response.json()['job']['runtimeConfig']['packageVersion']
        this_job.service_return_code = response.json()['job']['result']['serviceReturnCode']
        this_job.start_time = response.json()['job']['execStartTime']
        this_job.end_time = response.json()['job']['execEndTime']
        job_to_append = BatchJob(this_job.package_name, this_job.version, this_job.service_return_code,
                                 this_job.start_time, this_job.end_time)
        job_results_to_search.append(job_to_append)

    if len(job_results_to_search) < 1:
        print("No batch jobs of this type returned")
        return

    found_packages = []
    for job in range(len(job_results_to_search)):
        if job_results_to_search[job].package_name == package_to_search:
            found_packages.append(job_results_to_search[job])

    found_packages.sort(key=lambda x: x.start_time, reverse=True)

    # convert UNIX timestamps to something readable, timestamp is in milliseconds
    for row in range(len(found_packages)):
        st = int(found_packages[row].start_time)
        st /= 1000
        found_packages[row].start_time = (datetime.utcfromtimestamp(st).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
        et = int(found_packages[row].end_time)
        et /= 1000
        found_packages[row].end_time = (datetime.utcfromtimestamp(et).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])

    headers = ["Package Name", "Version", "Result", "Start Time", "End Time"]
    table = PrettyTable(headers)
    for row in range(len(found_packages)):
        table.add_row([found_packages[row].package_name, found_packages[row].version,
                       found_packages[row].service_return_code, found_packages[row].start_time,
                      found_packages[row].end_time])

    print(package_to_search)
    print(table)


def get_login_credentials(env):
    username = input("What is your {} Username?".format(env))
    password = input("What is your {} Password?".format(env))
    return username, password


env_interest = 0
env_options = ["1", "2", "3", "4"]
while env_interest not in env_options:
    if env_interest != 0:
        print("That is not a valid option. Please try again.")
    env_interest = input("What environment are you interested in? 1: FWS, 2: Dev1, 3: Dev2, 4: All  ")

use_fws = False
use_dev1 = False
use_dev2 = False
if env_interest in ["1", "4"]:
    use_fws = True
if env_interest in ["2", "4"]:
    use_dev1 = True
if env_interest in ["3", "4"]:
    use_dev2 = True

search_type = 0
search_type_options = ["1", "2", "3"]
while search_type not in search_type_options:
    if search_type != 0:
        print("That is not a valid option. Please try again.")
    search_type = input("What would you like? 1: List all packages, 2: Find batch executions, 3: Both  ")

list_all_packages = False
execute_search = False
if search_type in ["1", "3"]:
    list_all_packages = True
if search_type in ["2", "3"]:
    execute_search = True

if use_fws:
    fws_username, fws_password = get_login_credentials("FWS")
    if list_all_packages:
        get_all_packages_and_print_table("{}deploy-repo/packages".format(fws_url), "FWS", fws_username, fws_password)
    if execute_search:
        package_search = input(search_prompt)
        pull_batch_info("FWS", fws_url, package_search, fws_username, fws_password)
if use_dev1:
    dev1_username, dev1_password = get_login_credentials("Dev1")
    if list_all_packages:
        get_all_packages_and_print_table("{}deploy-repo/packages".format(dev1_url), "DEV1", dev1_username, dev1_password)
    if execute_search:
        package_search = input(search_prompt)
        pull_batch_info("DEV1", dev1_url, package_search, dev1_username, dev1_password)
if use_dev2:
    dev2_username, dev2_password = get_login_credentials("Dev2")
    if list_all_packages:
        get_all_packages_and_print_table("{}deploy-repo/packages".format(dev1_url), "DEV1", dev1_username, dev1_password)
    if execute_search:
        package_search = input(search_prompt)
        pull_batch_info("DEV2", dev2_url,package_search, dev2_username, dev2_password)
