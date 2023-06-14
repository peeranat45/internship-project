import argparse
from ipaddress import ip_address, IPv6Address

parser = argparse.ArgumentParser(prog='SDN Controller')
parser.add_argument('routerAddress')
parser.add_argument(metavar='rp', type=int, help='Router Port (default 8080)')
parser.add_argument(metavar='cp', type=int, help='Controller Port (default 8080)')


args = parser.parse_args()

# print(args.filename, args.count, type(args.verbose))

def validIPAddress(IP: str) -> str:
    try:
        return True if type(ip_address(IP)) is IPv6Address else False
    except ValueError:
        return "Invalid IP"



