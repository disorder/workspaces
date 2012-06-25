#!/usr/bin/env python
# Copyright (C) 2012  Adam Sloboda

## PROTOTYPE of independent "workspace" switching for 2 displays
# - uses XGrabKey to catch shortcuts (ctrl+f1..4, win+1..4, win+tab)
# - uses native workspaces, cuts them by displays and moves windows
# - workspace 0 is always active(!), 4 other workspaces are for saving windows
# there are commands:
# - set_loaded: set current loaded workspaces (restore after crash)
# - switch: independent switching for 2 displays
# - swap: swap windows on current native workspace between displays
# - swap_displays: swap any combination of display/workspace

from Xlib import display, X
from grab import grab_key
from manager import Manager

# TODO kinda lazy keyboard shortcuts (misses some?)
# TODO retain workspace numbers somehow (without touching disk)
# TODO netwmpager has trouble with updates, xfce4-panel is ok

## CONFIGURATION

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

if __name__ == "__main__":
    d = display.Display()

    # build dict from configuration
    keys = build_keys(shortcuts)
    keys[swap] = ('swap',)
    # grab keys
    for key, mod in keys:
        grab_key(d, mod, key)

    m = Manager(d)
    m.set_loaded(2,1)

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
                #m.switch(cmd[1], cmd[2])
                print m.loaded
