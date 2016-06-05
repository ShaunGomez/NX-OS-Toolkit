class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'
topics = [
color.CYAN + color.UNDERLINE + 'Informational' + color.END,
color.YELLOW + color.UNDERLINE + 'Change Scripts' + color.END,
color.GREEN + color.UNDERLINE + 'Standardization Scripts' + color.END
]
center = 80
l_align = 49
r_align = 50
header = '+' + '{:-^150}'.format(color.UNDERLINE +
	'NX-OS TOOLKIT'+color.END) + '+'
blank_body = '|' + '{:>143}'.format('|')
topic_body = '|' + '{0[0]:>{r_align}} {0[1]:^{center}} {0[2]:<{l_align}}'.format(
	topics, r_align=r_align, center=center, l_align=l_align) + '|'
body = """
|                        traffic                                 change                                    cdp                                 |
|                        topology                                verify                                                                        |
|                        sfpinventory                            drain                                                                         |
|                                                                isdrained                                                                     |
|                                                                undrain                                                                       |
"""
footer = '+' + '{:-^150}'.format(color.UNDERLINE +
	'For More Info: https://github.com/onenetworkguy/NX-OS-Toolkit'+color.END) + '+'

#MAIN Print
print header + '\n' + blank_body + '\n' + topic_body + body + blank_body + '\n' + footer
