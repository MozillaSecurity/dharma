#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import sys
import random
import logging
import argparse

from dharma.core import DharmaMachine
from dharma.websocket import DharmaWebSocketServer


class Dharma(object):
    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description='Dharma Runtime',
                                         prog='Dharma',
                                         add_help=False,
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                         epilog='The exit status is 0 for non-failures and -1 for failures.')
        m = parser.add_argument_group('mandatory arguments')
        m.add_argument('-grammars', metavar='file', type=argparse.FileType('r'), nargs='+', required=True,
                       help='input grammars')
        o = parser.add_argument_group('optional arguments')
        o.add_argument('-server', action='store_true', help='run in server mode')
        o.add_argument('-server-port', metavar='#', type=int, default=9090, help='server port')
        o.add_argument('-server-host', metavar='host', type=str, default='127.0.0.1', help='server address')
        o.add_argument('-storage', metavar='path', help='folder for test cases')
        o.add_argument('-format', metavar='ext', default='html', help='format of test cases')
        o.add_argument('-settings', metavar='file', type=argparse.FileType('r'),
                       default=os.path.relpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                            'settings.py')), help=" ")
        o.add_argument('-count', metavar='#', type=int, default=1, help='number of test cases')
        o.add_argument('-prefix', metavar='file', type=argparse.FileType('r'), help='prefix data')
        o.add_argument('-suffix', metavar='file', type=argparse.FileType('r'), help='suffix data')
        o.add_argument('-template', metavar='file', type=argparse.FileType('r'), help='template data')
        o.add_argument('-seed', metavar='#', type=int, default=os.getpid(), help='seed value for random')
        o.add_argument('-logging', metavar='#', default=10, type=int, choices=range(10, 60, 10),
                       help='verbosity level of logging')
        o.add_argument('-recursion-limit', metavar='#', type=int, default=20000, help='max python recursion limit')
        o.add_argument('-h', '-help', '--help', action='help', help=argparse.SUPPRESS)
        o.add_argument('-version', action='version', version='%(prog)s 1.0', help=argparse.SUPPRESS)
        return parser.parse_args()

    @classmethod
    def main(cls):
        args = cls.parse_args()
        sys.setrecursionlimit(args.recursion_limit)
        random.seed(args.seed)
        logging.basicConfig(format='[Dharma] %(asctime)s %(levelname)s: %(message)s', level=args.logging)
        logging.info("Machine random seed: %d", args.seed)
        prefix_data = "" if not args.prefix else args.prefix.read()
        suffix_data = "" if not args.suffix else args.suffix.read()
        template_data = "" if not args.template else args.template.read()
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


if __name__ == "__main__":
    sys.exit(Dharma.main())