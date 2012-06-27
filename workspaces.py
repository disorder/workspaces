#!/usr/bin/env python
# Copyright (C) 2012  Adam Sloboda

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

## CODE

def build_keys(shortcuts):
    keys = {}
    for monitor in xrange(len(shortcuts)):
        for mod, codes in (shortcuts[monitor],):
            for workspace in xrange(len(codes)):
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
    # grab keys
    for key, mod in keys:
        grab_key(d, mod, key)

    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hm:', ['help', 'mode='])
    except getopt.GetoptError, err:
        print str(err)
        exit(1)

    manager = Manager0
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            exit()
        elif o in ('-m', '--mode'):
            if a == 'full':
                manager = Manager
            elif a == 'part':
                manager = Manager0
            else:
                print 'invalid mode "%s"' % a
                usage()
                exit(1)
        else:
            assert False, "unhandled option"

    if manager == Manager:
        print 'using full workspaces: (N-1)*2 independent workspaces'
    elif manager == Manager0:
        print 'using partial workspaces: (N-1) independent workspaces'

    #m = Manager(d, os.path.expanduser('~'))
    m = manager(d, os.path.expanduser('~'))
    print m.loaded

    # set initial workspaces (useful after crash)
    if len(args) > 0:
        print 'setting initial workspaces to', args
        loaded = map(int, args)
        m.set_loaded(loaded)

    # process events
    while True:
        event = d.next_event()
        if event.type & X.KeyPressMask:
            try:
                cmd = keys[(event.state, event.detail)]
                print cmd
            except KeyError:
                continue

            if cmd[0] == 'swap':
                m.swap()
            elif cmd[0] == 'switch':
                m.switch(cmd[1], cmd[2])
                print m.loaded
