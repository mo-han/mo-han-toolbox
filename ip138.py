#!/usr/bin/env python

import requests
import argparse
from bs4 import BeautifulSoup


def query_geo(ip: str):
    url = 'http://www.ip138.com/ips138.asp?ip={}&action=2'.format(ip)
    soup = BeautifulSoup(requests.get(url).content, 'lxml')
    text_l = [li.text for li in soup.find('ul', class_='ul1')('li')]
    return text_l


def this_geo():
    url = 'http://www.ip138.com/'
    soup = BeautifulSoup(requests.get(url).content, 'lxml')
    url = soup.iframe['src']
    soup = BeautifulSoup(requests.get(url).content, 'lxml')
    return soup.body.text


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='ip138.com')
    ap.add_argument('ip', nargs='?', default='',
                    help='IP Address')
    ap.add_argument('-l', '--loop', action='store_true',
                    help='Loop mode, type in and query IPs one by one, type q to quit')
    ap.add_argument('-i', '--this', action='store_true',
                    help='Show IP and GeoInfo of this device')
    args = ap.parse_args()

    if args.loop:
        while True:
            ip = input('> ')
            if ip == 'q':
                exit(0)
            else:
                for i in query_geo(ip):
                    print(i)
    elif args.this:
        print(this_geo())
    elif args.ip:
        for i in query_geo(args.ip):
            print(i)
    else:
        print(this_geo())

