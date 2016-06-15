from cli import *
import json
import re

color_red="\x1b[31;01m"
color_green="\x1b[00;32m"
color_blue="\x1b[34;01m"
color_normal="\x1b[00m"

INTF_SHORT = re.compile(r'((.*)?Ethernet)')

def cdp_parser(cdp_neighbors):
	neigh_info = {}
	for neighbor in cdp_neighbors['TABLE_cdp_neighbor_detail_info']['ROW_cdp_neighbor_detail_info']:
		local_intf = neighbor['intf_id']
		neigh_name = neighbor['device_id'].split('.')[0].upper()
		platform = neighbor['platform_id'].lstrip('cisco ')
		neigh_ipv4 = neighbor['v4addr']
		remote_port = neighbor['port_id']
		remote_port = format_interface_strings(remote_port)
		neigh_info[local_intf] = dict(hostname = neigh_name, platform = platform, ipv4addr = neigh_ipv4, remote_intf = remote_port)
	return neigh_info

def create_config(neigh_info):
	config_list = []
	for intf in neigh_info.iterkeys():
	    interface_string = 'interface ' + intf
	    description_string = 'description {0[hostname]}_{0[remote_intf]}_{0[platform]}_{0[ipv4addr]}#MON'.format(neigh_info[intf])
	    config_dict = dict(interface = interface_string, description = description_string)
	    config_list.append(config_dict)
	return config_list

def apply_configuration(configuration):
	for config in configiguration:
		cli('configure terminal ; {0} ; {1}'.format(config['interface'], config['description']))

def format_interface_strings(remote_intf):
    ''' takes the str representation of the
    remote interface for a given CDP device and
    formats it to short notation.

    Example: GigbitEthernet = Gig
    Example: TenGigabitEthernet = Ten
    '''
    interface_mapper = dict(Ethernet='Eth', TenGigabitEthernet='Ten',
        GigabitEthernet='Gig', FastEthernet='Fa')
    short_name = INTF_SHORT.match(remote_intf)
    return remote_intf.replace(short_name.group(),
    	interface_mapper[short_name.group()]) if short_name else remote_intf

#MAIN
cdp_neighbors = json.loads(clid("show cdp neighbors detail"))
num_of_neigh = len(cdp_neighbors['TABLE_cdp_neighbor_detail_info']['ROW_cdp_neighbor_detail_info'])
neighbors = cdp_parser(cdp_neighbors)
configuration = create_config(neighbors)
print color_normal + "#" * 100
print color_green + "Found {0} Neighbors. The following configuration will be applied, are you sure? ( Yes or No ):".format(num_of_neigh)
print color_normal + "#" * 100 + '\n'
for config in configuration:
	print '\n'
	print color_normal + config['interface'] + '\n' + config['description']
answer = raw_input(color_green + "Please enter Yes or No: ")
if answer == 'Yes':
	apply_configuration(configuration)
	print color_normal + "#" * 100
	print color_green + "Configuration was applied! Don't forget to save!"
	print color_normal + "#" * 100
elif answer == 'No':
	print color_normal + "#" * 100
	print color_red + "Answer was No. Exiting"
	print color_normal + "#" * 100
else:
	print color_normal + "#" * 100
	print color_red + "Answer was not valid. Exiting"
	print color_normal + "#" * 100
