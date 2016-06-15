from cli import *
import json

transinfo = json.loads(clid("show interface transceiver"))

template = "{0:15} {1:15} {2:25} {3:15}"

def trans_interface_parser(transceiver):
	"""
	Parses an interface transceiver's dictionary and returns the following output
	if an SFP is present
	Port, Name, In Mbps, % In (rx load), Kpps, Out Mbps, % Out (tx load), Kpps
	"""
	output = ""
	if transceiver['sfp'] == 'present':
		output = template.format(transceiver['interface'], transceiver['type'], transceiver['serialnum'], transceiver['partnum'])
	else:
		return False
	return output

qsfp_bidi = 0
ten_gb_sr = 0
ten_gb_lr = 0
one_gb_mm = 0
one_gb_sm = 0
glc_t = 0

print "\n"
print "SFP Inventory: \n"
for transceiver in transinfo['TABLE_interface']['ROW_interface']:
	if transceiver['sfp'] == 'present':
		if transceiver['type'] == '10Gbase-SR':
			ten_gb_sr += 1
		elif transceiver['type'] == '10Gbase-LR':
			ten_gb_lr += 1
		elif transceiver['type'] == '1000base-SX':
			one_gb_mm += 1
		elif transceiver['type'] == '1000base-LH':
			one_gb_sm += 1
		elif transceiver['type'] == '1000base-T':
			glc_t += 1
		elif transceiver['type'] == 'QSFP+ bidi':
			qsfp_bidi += 1
	else:
		pass

print """
Number of 10Gbase-SR:  {0}
Number of 10Gbase-LR:  {1}
Number of 1000base-SX: {2}
Number of 1000base-LH: {3}
Number of 1000base-T:  {4}
""".format(ten_gb_sr, ten_gb_lr, one_gb_mm, one_gb_sm, glc_t)

#Print statements. Self explanatory.
print "\n"
print template.format("Port", "SFP Type", "SFP Serial Number", "SFP Part Number")
#For loop to iterate through interface list. Using try/except for error handling. Some interfaces don't have the keys we're interested in
#and will raise a key value error. Each interface is passed to eth_interface_parser if it has the matching keys. If it doesn't it is returned as False
#and not printed. This will return only physical interfaces and not the management interface.
for t in transinfo['TABLE_interface']['ROW_interface']:
	try:
		data = trans_interface_parser(t)
	except:
		data = False
	if data != False:
		print data
