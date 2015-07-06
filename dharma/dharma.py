#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import argparse
import logging
import os
import random
import struct
import sys

from core.dharma import DharmaMachine
from core.websocket import DharmaWebSocketServer


class Dharma(object):
    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(
            add_help=False,
            description='Dharma Runtime',
            epilog='The exit status is 0 for non-failures and -1 for failures.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog='Dharma'
        )

        m = parser.add_argument_group('mandatory arguments')
        m.add_argument('-grammars', metavar='file', type=argparse.FileType(), nargs='+', required=True,
                       help='input grammars')

        o = parser.add_argument_group('optional arguments')
        o.add_argument('-count', metavar='#', type=int, default=1, help='number of test cases')
        o.add_argument('-format', metavar='ext', default='html', help='format of test cases')
        o.add_argument('-h', '-help', '--help', action='help', help=argparse.SUPPRESS)
        o.add_argument('-logging', metavar='#', default=10, type=int, choices=range(10, 60, 10),
                       help='verbosity level of logging')
        o.add_argument('-prefix', metavar='file', type=argparse.FileType(), help='prefix data')
        o.add_argument('-recursion-limit', metavar='#', type=int, default=20000,
                       help='max python recursion limit')
        o.add_argument('-seed', metavar='#', type=int,
                       help='seed value for random, os.urandom will be used if not specified')
        o.add_argument('-server', action='store_true', help='run in server mode')
        o.add_argument('-server-host', metavar='host', type=str, default='127.0.0.1', help='server address')
        o.add_argument('-server-port', metavar='#', type=int, default=9090, help='server port')
        o.add_argument('-settings', metavar='file', type=argparse.FileType(),
                       default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.py'),
                       help='')
        o.add_argument('-storage', metavar='path', help='folder for test cases')
        o.add_argument('-suffix', metavar='file', type=argparse.FileType(), help='suffix data')
        o.add_argument('-template', metavar='file', type=argparse.FileType(), help='template data')
        o.add_argument('-version', action='version', version='%(prog)s 1.0', help=argparse.SUPPRESS)

        return parser.parse_args()

    @classmethod
    def main(cls):
        args = cls.parse_args()
        sys.setrecursionlimit(args.recursion_limit)
        logging.basicConfig(format='[Dharma] %(asctime)s %(levelname)s: %(message)s', level=args.logging)
        if args.seed is None:
            args.seed = struct.unpack('q', os.urandom(8))[0]
        random.seed(args.seed)
        logging.info('Machine random seed: %d', args.seed)
        prefix_data = '' if not args.prefix else args.prefix.read()
        suffix_data = '' if not args.suffix else args.suffix.read()
        template_data = '' if not args.template else args.template.read()
        dharma = DharmaMachine(prefix_data, suffix_data, template_data)
        dharma.process_settings(args.settings)
        dharma.process_grammars(args.grammars)
        if args.storage:
            dharma.generate_testcases(args.storage, args.format, args.count)
        elif args.server:
            server = DharmaWebSocketServer(dharma, (args.server_host, args.server_port))
            try:
                server.start()
            except KeyboardInterrupt:
                pass
            finally:
                server.stop()
        else:
            for _ in range(args.count):
                print(dharma.generate_content())
        return 0


if __name__ == '__main__':
    sys.exit(Dharma.main())
