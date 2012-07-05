# Copyright (C) 2012  Adam Sloboda

from Xlib import X

def error(*x): print 'error', x
def grab_key(display, mod, key, owner_events=False,
             pointer_mode=X.GrabModeAsync, keyboard_mode=X.GrabModeAsync,
             onerror=None):
    if not onerror:
        onerror = error
    display.screen().root.grab_key(key, mod, owner_events,
                                   pointer_mode, keyboard_mode, onerror)
