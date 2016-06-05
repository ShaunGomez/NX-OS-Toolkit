from cli import *
import json

color_red="\x1b[31;01m"
color_green="\x1b[00;32m"
color_blue="\x1b[34;01m"
color_normal="\x1b[00m"

def eigrp_neighbor_interfaces(eigrp_neighbors):
	eigrp_neighbor_int_list = []
	for neighbor in eigrp_neighbors['TABLE_asn']['ROW_asn']['TABLE_vrf']['ROW_vrf']['TABLE_peer']['ROW_peer']:
		eigrp_neighbor_int_list.append(neighbor['peer_ifname'])
	return eigrp_neighbor_int_list

def is_drained(interfaces):
	for interface in interfaces:
		interface_info = json.loads(clid("show interface {}".format(interface)))
		if int(interface_info['TABLE_interface']['ROW_interface']["eth_inrate1_bits"]) and int(interface_info['TABLE_interface']['ROW_interface']["eth_outrate1_bits"]) > 100000:
			print color_red + "{} is not drained of traffic".format(interface)
		elif int(interface_info['TABLE_interface']['ROW_interface']["eth_inrate1_bits"]) and int(interface_info['TABLE_interface']['ROW_interface']["eth_outrate1_bits"]) <= 100000:
			print color_green + "{} is drained of traffic".format(interface)

#MAIN
eigrp_neighbors = eigrp_neighbor_interfaces(json.loads(clid("show ip eigrp neighbors")))
is_drained(eigrp_neighbors)