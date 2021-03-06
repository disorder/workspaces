#!/usr/bin/env python
# Copyright (C) 2012  Adam Sloboda

import logging
from Xlib import display, X
from grab import grab_key
from manager import Manager, Manager0
import sys, os


## CONFIGURATION

# don't forget to unbind them in other software (xbindkeys, xfwm4)

# keys as reported by xev program
shortcuts = ( # 2 displays
    # ctrl+f1..f4
    (X.ControlMask, [ 67, 68, 69, 70 ]),
    # win+1..4
    (X.Mod4Mask, [ 10, 11, 12, 13 ])
)

# win+tab
swap = (X.Mod4Mask, 23)
# win+`
clear = (X.Mod4Mask, 49)

## CODE

def build_keys(shortcuts):
    keys = {}
    for monitor in range(len(shortcuts)):
        for mod, codes in (shortcuts[monitor],):
            for workspace in range(len(codes)):
                keys[(mod, codes[workspace])] = ('switch', monitor, workspace+1)
    return keys

def usage():
    print("Usage: %s options [initial workspaces]\n" % sys.argv[0])
    print(" -h --help               Display this usage information.\n"
          " -m --mode <full|part>   Manager mode.\n")

if __name__ == "__main__":
    d = display.Display()

    # build dict from configuration
    keys = build_keys(shortcuts)
    keys[swap] = ('swap',)
    keys[clear] = ('clear',)
    # grab keys
    for mod, key in keys:
        grab_key(d, mod, key)
        # add caps and num lock combinations
        grab_key(d, mod | X.LockMask, key)
        grab_key(d, mod | X.Mod2Mask, key)
        grab_key(d, mod | X.LockMask | X.Mod2Mask, key)

    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hL:m:', ['help', 'loglevel=', 'mode='])
    except getopt.GetoptError as err:
        print(str(err))
        exit(1)

    manager = Manager0
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            exit()
        elif o in ('-L', '--loglevel'):
            logging.getLogger().setLevel(a)
        elif o in ('-m', '--mode'):
            if a == 'full':
                manager = Manager
            elif a == 'part':
                manager = Manager0
            else:
                print('invalid mode "%s"' % a)
                usage()
                exit(1)
        else:
            assert False, "unhandled option"

    if manager == Manager:
        print('using full workspaces: (N-1)*2 independent workspaces')
    elif manager == Manager0:
        print('using partial workspaces: (N-1) independent workspaces')

    #m = Manager(d, os.path.expanduser('~'))
    m = manager(d, os.path.expanduser('~'))
    print(m.loaded)

    # set initial workspaces (useful after crash)
    if len(args) > 0:
        print('setting initial workspaces to', args)
        loaded = list(map(int, args))
        m.set_loaded(loaded)

    # process events
    while True:
        event = d.next_event()
        if event.type & X.KeyPressMask:
            try:
                # ignore caps and num lock
                state = event.state & ~X.LockMask & ~X.Mod2Mask
                cmd = keys[(state, event.detail)]
                logging.debug(cmd)
            except KeyError:
                continue

            if cmd[0] == 'swap':
                m.swap()
            elif cmd[0] == 'clear':
                # clears right display
                m.clear()
            elif cmd[0] == 'switch':
                m.switch(cmd[1], cmd[2])
                #print(m.loaded)
