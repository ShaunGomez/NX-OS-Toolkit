from cli import *
import json

color_red="\x1b[31;01m"
color_green="\x1b[00;32m"
color_blue="\x1b[34;01m"
color_normal="\x1b[00m"

def eigrp_undrain_config(eigrp_neighbors):
	config_list = []
	for neighbor in eigrp_neighbors['TABLE_asn']['ROW_asn']['TABLE_vrf']['ROW_vrf']['TABLE_peer']['ROW_peer']:
		config_dict = dict(interface = 'interface {}'.format(neighbor['peer_ifname']), no_delay = "no delay")
		config_list.append(config_dict)
	return config_list

def apply_configuration(configuration):
	for config in config_list:
		cli('configure terminal ; {0} ; {1}'.format(config['interface'], config['no_delay']))

def find_eigrp_peers(eigrp_info):
	number_eigrp_peers = eigrp_info['TABLE_asn']['ROW_asn']['TABLE_vrf']['ROW_vrf'][1]['num_peers']
	return number_eigrp_peers

#MAIN
configuration = eigrp_undrain_config(json.loads(clid("show ip eigrp neighbors")))
num_of_peers = find_eigrp_peers(json.loads(clid("show ip eigrp")))
print color_normal + "#" * 100
print color_green + "Found {0} Neighbors. The following configuration will be applied, are you sure? ( Yes or No ):".format(num_of_peers)
print color_normal + "#" * 100 + '\n'
for config in configuration:
	print color_normal + config['interface'] + '\n' + config['no_delay']
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