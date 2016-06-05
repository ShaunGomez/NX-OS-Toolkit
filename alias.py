from cli import *
import re

PY_PARSER = re.compile(r'(\w+).py$')

def find_scripts(scripts):
	script_list = []
	for script in scripts.splitlines():
		x = PY_PARSER.search(script)
		if x:
			script_list.append(x.group())
	return script_list

def apply_cli_alias(script_list):
	if 'cdp.py' in script_list:
		cli('configure terminal ; cli alias name {} python bootflash:scripts/cdp.py'.format('cdp'))
	if 'change.py' in script_list:
		cli('configure terminal ; cli alias name {} python bootflash:scripts/change.py'.format('change'))
	if 'verify.py' in script_list:
		cli('configure terminal ; cli alias name {} python bootflash:scripts/verify.py'.format('verify'))
	if 'drain.py' in script_list:
		cli('configure terminal ; cli alias name {} python bootflash:scripts/drain.py'.format('drain'))
	if 'is_drained.py' in script_list:
		cli('configure terminal ; cli alias name {} python bootflash:scripts/is_drained.py'.format('isdrained'))
	if 'undrain.py' in script_list:
		cli('configure terminal ; cli alias name {} python bootflash:scripts/undrain.py'.format('undrain'))
	if 'traffic.py' in script_list:
		cli('configure terminal ; cli alias name {} python bootflash:scripts/traffic.py'.format('traffic'))
	if 'transceiver_inventory.py' in script_list:
		cli('configure terminal ; cli alias name {} python bootflash:scripts/transceiver_inventory.py'.format('sfpinventory'))
	if 'toolkit.py' in script_list:
		cli('configure terminal ; cli alias name {} python bootflash:scripts/toolkit.py'.format('toolkit'))

def alias():
	alias = cli('alias')
	for line in alias.splitlines():
		print line

#MAIN
scripts = find_scripts(cli('dir bootflash:scripts'))
apply_cli_alias(scripts)
print "The following CLI alias commands have been created:"
alias()