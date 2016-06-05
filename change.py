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

def save_state(fname, change_id):
	commands = [
	'dir',
	'show version',
	'show license usage',
	'show module',
	'show inventory',
	'show environment',
	'show processes cpu history',
	'show system resources',
	'show system uptime',
	'show feature',
	'show cfs peers',
	'show cfs application',
	'show cfs status',
	'show cfs lock',
	'show copp status',
	'show ip route',
	'show ip arp',
	'show mac address-table dynamic',
	'show ip interface brief',
	'show interface',
	'show interface status',
	'show cdp neighbors',
	'show spanning-tree',
	'show spanning-tree root',
	]

	print color_blue + "Saving the following output to bootflash:{0}/{1}".format(change_id, fname)
	for command in commands:
		print color_normal + command
		cli(command + ' >> bootflash:{0}/{1}'.format(change_id, fname))

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

def save_features_state_to_flash(enabled_features, fname, change_id):

	if 'eigrp' in enabled_features:

		eigrp_commands = [
		'show ip eigrp',
		'show ip eigrp neighbors',
		'show ip eigrp topology detail-links',
		'show ip eigrp accounting',
		]

		print color_blue + "EIGRP is enabled. Saving the following output to bootflash:{0}/{1}".format(change_id, fname)

		for command in eigrp_commands:
			print color_normal + command
			cli(command + ' >> bootflash:{0}/{1}'.format(change_id, fname))

	if 'bfd' in enabled_features:

		bfd_commands = [
		'show bfd neighbors',
		'show bfd neighbors detail',
		]

		print color_blue + "BFD is enabled. Saving the following output to bootflash:{0}/{1}".format(change_id, fname)
		
		for command in bfd_commands:
			print color_normal + command
			cli(command + ' >> bootflash:{0}/{1}'.format(change_id, fname))

	if 'hsrp_engine' in enabled_features:
		
		hsrp_commands = [
		'show hsrp',
		'show hsrp summary',
		'show hsrp detail',
		]

		print color_blue + "HSRP is enabled. Saving the following output to bootflash{0}/{1}".format(change_id, fname)

		for command in hsrp_commands:
			print color_normal + command
			cli(command + ' >> bootflash:{0}/{1}'.format(change_id, fname))

	if 'interface-vlan' in enabled_features:

		vlan_commands = [
		'show vlan brief',
		'show spanning-tree',
		'show spanning-tree detail',
		'show spanning-tree root',
		'show spanning-tree blockedports',
		'show spanning-tree active',
		]

		print color_blue + "Interface-vlan is enabled. Saving the following output to bootflash:{0}/{1}".format(change_id, fname)

		for command in vlan_commands:
			print color_normal + command
			cli(command + ' >> bootflash:{0}/{1}'.format(change_id, fname))

	if 'lacp' in enabled_features:
		
		lacp_commands = [
		'show port-channel summary',
		'show port-channel usage',
		]

		print color_blue + "LACP is enabled. Saving the following output to bootflash:{0}/{1}".format(change_id, fname)

		for command in lacp_commands:
			print color_normal + command
			cli(command + ' >> bootflash:{0}/{1}'.format(change_id, fname))

	if 'pim' in enabled_features:

		pim_commands = [
		'show ip pim neighbor',
		'show ip pim rp',
		'show ip mroute',
		'show ip mroute summary',
		]

		print color_blue + "PIM is enabled. Saving the following output to bootflash:{0}/{1}".format(change_id, fname)

		for command in pim_commands:
			print color_normal + command
			cli(command + ' >> bootflash:{0}/{1}'.format(change_id, fname))

def create_checkpoint(fname, change_id):
	print color_green + "Creating checkpoint: %s" % fname
	cli("checkpoint {0} description Checkpoint created by change.py for {1}".format(fname, change_id))

def send_email(fname, user_id):
	print color_green + "Sending e-mail to {0}@navyfederal.org".format(user_id) + " this may take a moment..."
	email = cli("show file {0} | email subject {1}_show_ouput {2}@navyfederal.org".format(fname, fname, user_id))
	if email == "Error in sending email\n":
		print color_red + "Email did not send. Please check if email if configured."
		print color_normal + """
		If email settings are configured try resending via cli "show file {0} | email subject {1}_show_ouput {2}@navyfederal.org"
		""".format(fname, fname, user_id)


#MAIN
user_id = os.getlogin()
host = socket.gethostname()
date = date.today()
print "Hello %s!" % user_id
change_id = raw_input('Please Enter Change Number: ')
fname = '{0}_{1}_{2}_{3}'.format(change_id, user_id, host, str(date))
user_dir = '/var/home/%s' % user_id

call(["mkdir", "/bootflash/%s" % change_id])

if not os.getcwd() == user_dir:
	os.chdir(user_dir)

save_state(fname, change_id)
features = json.loads(clid("show feature"))
enabled_features = find_enabled_features(features)
save_features_state_to_flash(enabled_features, fname, change_id)
eigrp_state, bfd_state, pim_state = features_state(enabled_features)
state = {
		'eigrp' : eigrp_state,
		'bfd' : bfd_state,
		'pim' : pim_state,
		}

#send_email(fname, user_id)
create_checkpoint(fname, change_id)

with open(fname + '.pkl', 'w') as state_pkl:
	pickle.dump(state, state_pkl, protocol=pickle.HIGHEST_PROTOCOL)

call(["mv", user_dir + '/' + fname + '.pkl', "/bootflash/%s" % change_id])