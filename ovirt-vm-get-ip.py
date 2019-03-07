#! /usr/bin/env python

import logging
import sys
import time
import re
from optparse import OptionParser

import ovirtsdk4 as sdk

DEFAULT_API_USER = "admin@internal"
DEFAULT_SUBNET_PREFIX_PATTERN = "10.60.28."
DEFAULT_TIMEOUT = 10

def parse_args():
    parser = OptionParser(description='Get the IP of a running VM')

    parser.add_option('--debug', action='store_true', default=False, help='debug mode')
    parser.add_option('--api_url', default=None, help='oVirt API IP Address/Hostname')
    parser.add_option( '--api_user', default=DEFAULT_API_USER, help='oVirt API Username, defaults to "%s"' % (DEFAULT_API_USER))
    parser.add_option('--api_pass', default=None, help='oVirt API Password')
    parser.add_option('--vm_id', default=None, help='ID of an existing VM to add a disk to')
    parser.add_option( '--subnet_prefix', default=DEFAULT_SUBNET_PREFIX_PATTERN, help='Subnet the vm\'s IP is belonging to, defaults to "%s"' % (DEFAULT_SUBNET_PREFIX_PATTERN))
    parser.add_option( '--timeout', default=DEFAULT_TIMEOUT, help='The IP retrieving timeout, defaults to "%s"' % (DEFAULT_TIMEOUT))
    (opts, args) = parser.parse_args()

    for optname in ["api_url", "api_pass", "api_user", "vm_id"]:
        optvalue = getattr(opts, optname)
        if not optvalue:
            parser.print_help()
            parser.print_usage()
            print "Please re-run with an option specified for: '%s'" % (optname)
            sys.exit(1)

    return opts

def setup_logging(debug=False):
    if debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')

def get_vm_ip(connection, vm_id):
    vms_service = connection.system_service().vms_service()
    vm = vms_service.vm_service(vm_id)
    devices = vm.reported_devices_service().list()
    if len(devices) > 0:

        vm_ip = None 

        for device in devices:
            if device.ips:
                for ip in device.ips:
                    vm_ip = re.search(subnet_prefix, ip.address)
                    if vm_ip:
                        return(ip.address)
            else:
                print("Can't find any IP up for vm '%s'!" % (vm_id))
                return None

        if vm_ip is None:
            print("Can't find any active IP matching the target subnet prefix '%s'" % (subnet_prefix))
            return None
    else:
        print("Can't find the network interfaces for vm '%s'!" % (vm_id))
        return None

if __name__ == "__main__":
    opts = parse_args()
    debug = opts.debug
    setup_logging(debug)

    api_url = opts.api_url
    api_user = opts.api_user
    api_pass = opts.api_pass
    vm_id = opts.vm_id
    subnet_prefix = opts.subnet_prefix

    timeout = int(opts.timeout)
    wait_secs = 5
    iterations = timeout/wait_secs

    ip = None

    connection = sdk.Connection(url=api_url, username=api_user, password=api_pass, insecure=True)
    if not connection:
        print "Failed to connect to '%s'" % (url)
        sys.exit(1)

    for count in range(0, iterations):
        ip = get_vm_ip(connection, vm_id)
        if not ip:
            print("Sleeping for '%s' seconds..." % (wait_secs))
            logging.debug("Waiting %s seconds for IP to become available of VM ID '%s' (%s/%s)" % (wait_secs, vm_id, count, iterations))
            time.sleep(wait_secs)
        else:
            print(ip)
            connection.close()
            sys.exit(0)

    if not ip:
        print("Failed find the IP for the VM!")
        connection.close()
        sys.exit(127)
