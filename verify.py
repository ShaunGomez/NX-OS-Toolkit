from cli import *
import json
from datetime import date
import os
import subprocess
from subprocess import call
import pickle
import socket

color_red="\x1b[31;01m"
color_green="\x1b[00;32m"
color_blue="\x1b[34;01m"
color_normal="\x1b[00m"

def find_enabled_features(features):
	enabled_features = []
	for feature in features['TABLE_cfcFeatureCtrlTable']['ROW_cfcFeatureCtrlTable']:
		if feature['cfcFeatureCtrlOpStatus2'] == 'enabled':
			enabled_features.append(feature['cfcFeatureCtrlName2'])
	return enabled_features

def dict_compare(d1, d2):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    modified = {o : (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
    return modified

def features_state(enabled_features):
	if 'eigrp' in enabled_features:
		eigrp_neigh_int = []
		eigrp_info = json.loads(clid("show ip eigrp"))
		number_eigrp_peers = eigrp_info['TABLE_asn']['ROW_asn']['TABLE_vrf']['ROW_vrf'][1]['num_peers']
		number_eigrp_int = eigrp_info['TABLE_asn']['ROW_asn']['TABLE_vrf']['ROW_vrf'][1]['num_interfaces'][0]
		eigrp_neighbors = json.loads(clid("show ip eigrp neighbors"))
		for neighbor in eigrp_neighbors['TABLE_asn']['ROW_asn']['TABLE_vrf']['ROW_vrf']['TABLE_peer']['ROW_peer']:
			eigrp_neigh_int.append(neighbor['peer_ifname'])
		eigrp_accounting = json.loads(clid("show ip eigrp accounting"))
		eigrp_acc_info = eigrp_accounting['TABLE_asn']['ROW_asn']['TABLE_vrf']['ROW_vrf']
		total_prefix = eigrp_acc_info[1]['total_prefix']
		eigrp_peers_info = {}
		eigrp_peers = []
		for peer in eigrp_acc_info[1]['TABLE_peer']['ROW_peer'][1:]:
			peer_intf = peer['p_ifname']
			eigrp_peers_info[peer_intf] = dict(peer = peer['p_ipaddr'], prefix_count = peer['p_prefix_count'])
			eigrp_peers.append(peer['p_ipaddr'])
		eigrp_state = {
			'neighbor_interfaces' : eigrp_neigh_int,
			'num_peers' : number_eigrp_peers,
			'num_interfaces' : number_eigrp_int,
			'num_prefixes' : total_prefix,
			'peers' : eigrp_peers,
			'peer_info' : eigrp_peers_info 
		}
	if 'bfd' in enabled_features:
		bfd_neighbors = json.loads(clid("show bfd neighbors"))
		num_peers = 0
		bfd_neigh_int = []
		bfd_neigh_ip = []
		for neigh in bfd_neighbors['TABLE_bfdNeighbor']['ROW_bfdNeighbor']:
			if neigh['remote_state'] == 'Up':
				bfd_neigh_int.append(neigh['intf'])
				bfd_neigh_ip.append(neigh['dest_ip_addr'])
				num_peers += 1
		bfd_state = {
			'interfaces' : bfd_neigh_int,
			'peers' : bfd_neigh_ip,
			'num_peers' : num_peers
		}
	#Add state for hsrp
	#if 'hsrp_engine' in enabled_features:
	#Add state for interface-vlan
	#if 'interface-vlan' in enabled_features:
	#Add state for lacp
	#if 'lacp' in enabled_features:
	if 'pim' in enabled_features:
		pim_neighbors = json.loads(clid("show ip pim neighbor"))
		pim_neigh_int = []
		pim_neigh_ip = []
		for neighbor in pim_neighbors['TABLE_iod']['ROW_iod'][1:-1]:
			pim_neigh_int.append(neighbor['if-name'])
			pim_neigh_ip.append(neighbor['TABLE_neighbor']['ROW_neighbor'][1]['nbr-addr'])
		pim_rp = json.loads(clid("show ip pim rp"))
		pim_rp_addr = pim_rp['TABLE_rp']['ROW_rp']['rp-addr']
		mroute_table = json.loads(clid("show ip mroute"))
		mcast_addrs = []
		for mroute in mroute_table['TABLE_vrf']['ROW_vrf']['TABLE_one_route']['ROW_one_route']:
			mcast_addrs.append(mroute['mcast-addrs'])
		mroute_summary = json.loads(clid("show ip mroute summary"))
		num_mcast_routes = mroute_summary['TABLE_vrf']['ROW_vrf']['TABLE_route_summary']['ROW_route_summary']['total-num-routes']
		num_mcast_groups = mroute_summary['TABLE_vrf']['ROW_vrf']['TABLE_route_summary']['ROW_route_summary']['group-count']
		num_star_g_routes = mroute_summary['TABLE_vrf']['ROW_vrf']['TABLE_route_summary']['ROW_route_summary']['star-g-route']
		num_sg_routes = mroute_summary['TABLE_vrf']['ROW_vrf']['TABLE_route_summary']['ROW_route_summary']['sg-route']
		mcast_srcnum_group = []
		for mcast_source in mroute_summary['TABLE_vrf']['ROW_vrf']['TABLE_summary_source']['ROW_summary_source']:
			mcast_srcnum_group .append((mcast_source['source_count'], mcast_source['group_addr']))
		pim_state = {
			'neigh_int' : pim_neigh_int,
			'neigh_ip' : pim_neigh_ip,
			'rp' : pim_rp_addr,
			'mroutes' : mcast_addrs,
			'num_mroutes' : num_mcast_routes,
			'num_mgroups' : num_mcast_groups,
			'num_star_g' : num_star_g_routes,
			'num_source_g' : num_sg_routes,
			'src_count' : mcast_srcnum_group
		}
	return eigrp_state, bfd_state, pim_state

def verify_eigrp(pre_eigrp_state, post_eigrp_state):
	print color_green + '\n' + "#" * 100 + '\n' + "Verifying EIGRP..." + '\n' + "#" * 100 + '\n'

	if pre_eigrp_state['num_peers'] == post_eigrp_state['num_peers']:
		print color_normal + """Total number of EIGRP peers before change: {0} \nTotal number of EIGRP peers after change: {1}
		""".format(pre_eigrp_state['num_peers'], post_eigrp_state['num_peers'])
	else:
		missing_peer = set(pre_eigrp_state['peers']) - set(post_eigrp_state['peers'])
		print color_red + '!' * 100
		print color_red + "The following peers are missing EIGRP adjancency:"
		for peer in list(missing_peer):
			print color_normal + peer

	if pre_eigrp_state['num_prefixes'] == post_eigrp_state['num_prefixes']:
		print color_normal + """Total number of EIGRP prefixes before change: {0} \nTotal number of EIGRP prefixes after change: {1}
		""".format(pre_eigrp_state['num_prefixes'], post_eigrp_state['num_prefixes'])
	else:
		missing_eigrp_prefixes(pre_eigrp_state, post_eigrp_state)

	if pre_eigrp_state['neighbor_interfaces'] == post_eigrp_state['neighbor_interfaces']:
		print color_normal + "\nEIGRP neighbor interface results: " + color_green + "Success!"
	else:
		missing_int = set(pre_eigrp_state['neighbor_interfaces']) - set(post_eigrp_state['neighbor_interface'])
		print color_red + '!' * 100
		print color_red + "The following interfaces are missing EIGRP configuration:"
		for interface in list(missing_int):
			print color_normal + interface

	print color_green + '\n' + "#" * 100 + '\n' + "Completed EIGRP verification." + '\n' + "#" * 100 + '\n'

def missing_eigrp_prefixes(pre_eigrp_state, post_eigrp_state):
	difference = dict_compare(pre_eigrp_state, post_eigrp_state)
	if not difference:
		print color_green + "Post change prefix count match pre-change prefix count!"
	else:
		for diff in difference.items():
			num_prefixes_missing = abs(int(diff[1][0]['prefix_count']) - int(diff[1][1]['prefix_count']))
			print color_red + "Missing {0} prefixes from {1}.".format(num_prefixes_missing, diff[1][0]['peer'])

def verify_bfd(pre_bfd_state, post_bfd_state):
	print color_green + '\n' + "#" * 100 + '\n' + "Verifying BFD..." + '\n' + "#" * 100 + '\n'
	if pre_bfd_state['num_peers'] == post_bfd_state['num_peers']:
		print color_normal + """Total number of BFD neighbors before change: {0} \nTotal number of BFD neighbors after change: {1}
		""".format(pre_bfd_state['num_peers'], post_bfd_state['num_peers'])
	if pre_bfd_state['peers'] == post_bfd_state['peers']:
		print color_normal + "BFD neighbor results: " + color_green + "Success!"
	else:
		missing_peer = set(pre_bfd_state['peers']) - set(post_bfd_state['peers'])
		print color_red + '!' * 100
		print color_red + "The following BFD neighbors are missing:"
		for peer in list(missing_peer):
			print color_normal + peer
		missing_int = set(pre_bfd_state['interfaces']) - set(post_bfd_state['interfaces'])
		print color_red + '!' * 100
		print color_red + "The following BFD interfaces are missing:"
		for interface in list(missing_int):
			print color_normal + interface

	print color_green + '\n' + "#" * 100 + '\n' + "Completed BFD verification." + '\n' + "#" * 100 + '\n'

def verify_pim(pre_pim_state, post_pim_state):
	print color_green + '\n' + "#" * 100 + '\n' + "Verifying PIM" + '\n' + "#" * 100 + '\n'
	if pre_pim_state['neigh_ip'] == post_pim_state['neigh_ip']:
		print color_normal + "PIM neighbor results: " + color_green + "Success!"
	else:
		missing_peer = set(pre_pim_state['neigh_ip']) - set(post_pim_state['neigh_ip'])
		print color_red + '!' * 100
		print color_red + "The following PIM neighbors are missing:"
		for peer in list(missing_peer):
			print color_normal + peer

	print color_green + '\n' + "#" * 100 + '\n' + "Completed PIM verification." + '\n' + "#" * 100 + '\n'

def verify_features(enabled_features, pre_eigrp_state, post_eigrp_state,
					pre_bfd_state, post_bfd_state, pre_pim_state, post_pim_state):
	if 'eigrp' in enabled_features:
		verify_eigrp(pre_eigrp_state, post_eigrp_state)
	if 'bfd' in enabled_features:
		verify_bfd(pre_bfd_state, post_bfd_state)
	if 'pim' in enabled_features:
		verify_pim(pre_pim_state, post_pim_state)

#MAIN
user_id = os.getlogin()
host = socket.gethostname()
date = date.today()
print "Hello %s!" % user_id
change_id = raw_input('Please Enter Change Number: ')
fname = '{0}_{1}_{2}_{3}'.format(change_id, user_id, host, str(date))
chg_dir = '/bootflash/{0}'.format(change_id)

if not os.getcwd() == chg_dir:
	os.chdir(chg_dir)

pre_change_state = pickle.load(open(fname + '.pkl', 'rb'))
enabled_features = find_enabled_features(json.loads(clid("show feature")))
post_eigrp_state, post_bfd_state, post_pim_state = features_state(enabled_features)

verify_features(enabled_features, pre_change_state['eigrp'], post_eigrp_state,
	pre_change_state['bfd'], post_bfd_state, pre_change_state['pim'], post_pim_state)

print color_normal + '\n' * 3 + "Validation has been completed!"