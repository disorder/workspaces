# Copyright (C) 2012  Adam Sloboda
# inspired by wmctrl and pywo code
# more messages: http://standards.freedesktop.org/wm-spec/1.3/ar01s03.html

from Xlib.protocol.event import ClientMessage
from Xlib import X

def send_event(disp, win, data, event_type, mask):
    event = ClientMessage(window=win, client_type=event_type, data=(32, (data)))
    return disp.screen().root.send_event(event, event_mask=mask)

def get_property(disp, name):
    atom = disp.intern_atom(name)
    return disp.screen().root.get_full_property(atom, 0)

def get_window_property(disp, name, window):
    atom = disp.intern_atom(name)
    return disp.create_resource_object('window', window).get_full_property(atom, 0)

def get_property_value(disp, name):
    return get_property(disp, name).value[0]

def get_window_property_value(disp, name, window):
    return get_window_property(disp, name, window).value[0]

# x,y,w,h = -1 if not changing
def moveresize(disp, window, x=-1,y=-1,w=-1,h=-1, grav=0):
    event_type = disp.intern_atom('_NET_MOVERESIZE_WINDOW')
    mask = X.SubstructureRedirectMask | X.SubstructureNotifyMask
    grflags = grav;
    if x != -1: grflags |= (1 << 8)
    if y != -1: grflags |= (1 << 9)
    if w != -1: grflags |= (1 << 10)
    if h != -1: grflags |= (1 << 11)
    data = [grflags, max(x, 0), max(y, 0), max(w, 0), max(h, 0)]
    return send_event(disp, window, data, event_type, mask)

# send window to another desktop
def set_desktop(disp, window, desktop):
    event_type = disp.intern_atom('_NET_WM_DESKTOP')
    mask = X.PropertyChangeMask
    data = [desktop, 0, 0, 0, 0]
    return send_event(disp, window, data, event_type, mask)

# which desktop is window on
def get_desktop(disp, window):
    return get_window_property_value(disp, '_NET_WM_DESKTOP', window)

def set_active_window(disp, window):
    event_type = disp.intern_atom('_NET_ACTIVE_WINDOW')
    mask = X.PropertyChangeMask
    data = [0, 0, 0, 0, 0]
    return send_event(disp, window, data, event_type, mask)

def get_active_window(disp):
    return get_property_value(disp, '_NET_ACTIVE_WINDOW')

def get_number_of_desktops(disp):
    return get_property_value(disp, '_NET_NUMBER_OF_DESKTOPS')

def get_current_desktop(disp):
    return get_property_value(disp, '_NET_CURRENT_DESKTOP')
    # also
    #get_property_value(disp, '_WIN_WORKSPACE')

def get_pid(disp, window):
    return get_window_property_value(disp, '_NET_WM_PID', window)

def get_windows(disp):
    return get_property(disp, '_NET_CLIENT_LIST').value

def get_geometry(disp, window):
    w = disp.create_resource_object('window', window)
    w.map()
    g = w.get_geometry()
    t = g.root.translate_coords(w, g.x, g.y)
    return (t.x, t.y, g.width, g.height, g.x, g.y)

# apply changes
def commit(disp):
    # they get applied upon close or any reading, reopen is slower
    get_current_desktop(disp)

if __name__ == "__main__":
    from Xlib import display
    disp = display.Display()
    print get_active_window(disp)
    print get_current_desktop(disp), get_number_of_desktops(disp)
    print get_property(disp, '_NET_DESKTOP_NAMES').value.split('\x00')
    print get_property(disp, '_NET_CLIENT_LIST').value

    #moveresize(disp, 65354518, 50, 420, 580, 320)
    moveresize(disp, 65354518, 50, 420, -1, -1)

    #print set_desktop(disp, 65354518, 3)
    # get desktop ID of window (makes window_to_desktop work?)
    #print get_window_property_value(disp, '_NET_WM_DESKTOP', 65354518)
    # or this activates change
    #disp.create_resource_object('window', 65354518).map()
    #disp.create_resource_object('window', disp.screen().root).map()
    # or this:
    #disp.close()

    #set_active_window(disp, 0x00e00013)
    #disp.create_resource_object('window', 0x00e00013).raise_window()
    #set_active_window(disp, 65354518)
    # this also makes work set_active_window and returns value
    #print get_active_window(disp)

    #print get_pid(disp, 0x00e00013)
    #print get_desktop(disp, 0x00e00013)

    #print get_geometry(disp, 0x00e00013)
    # there are more (border_width)
    #print disp.create_resource_object('window', 0x00e00013).get_geometry()

    for win in get_windows(disp):
        workspace = get_desktop(disp, win)
        if workspace != 0xffffffff:
            print get_geometry(disp, win)
        print '%08x %08x' % (workspace, win)
        # 0xffffffff: show on all desktops

    # apply changes
    disp.close()
    # (they get applied upon close or any reading, reopen is slower)
    #get_current_desktop(disp)
