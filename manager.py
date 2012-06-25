# Copyright (C) 2012  Adam Sloboda

from Xlib import display
from screen import Screen
import subprocess
import re
import xlib

# TODO retain window focus?
# TODO why are reported values +10 and +46?
# x = 10 = 2x5 = 5 is w of window border
# y = 46 = 2x23 = 23 is h of window title bar
# (both reported as .x/.y geometry, is this correct?)

def run(cmd):
    #subprocess.Popen(cmd.split())
    # we have to wait because we need to process sequentially
    subprocess.call(cmd.split())

def output(cmd):
    return subprocess.Popen(cmd.split(),stdout=subprocess.PIPE).communicate()[0]
    # Python 2.7
    #subprocess.check_output(cmd.split())

class Window:
    def __init__(self,win,x,y,w,h,xrel,yrel,display):
        self.id = win
        self.x, self.y, self.w, self.h, self.xrel, self.yrel = x,y,w,h,xrel,yrel
        self.d = display

class Manager:
    def __init__(self, display):
        # windows will be moved to workspace 1 when switching
        self.loaded = [1, 1]
        self.history = [None, None]
        self.focus = [4*[None], 4*[None]]

        self.display = display
        # currently not really needed, event processing is sequential

    # load current WM state
    def update(self):
        self.update_screens()
        self.update_workspaces()
        self.update_windows()        

    # set arbitrary state for loaded desktop
    def set_loaded(self, a, b):
        self.loaded = [a, b]

    # implemented for horizontal non-overlapping views
    # returns corresponding display for window
    def get_screen(self, x):
        for i in xrange(len(self.screens)):
            # TODO maybe include also 5-10 pixels less than Screen.w?
            if x - self.screens[i].x < self.screens[i].w:
                return i

    # update window list
    def update_windows(self):
        for win in xlib.get_windows(self.display):
            d = xlib.get_desktop(self.display, win)
            if d != 0xffffffff:
                geom = xlib.get_geometry(self.display, win)
                screen = self.get_screen(geom[0])
                # win_id, x, y, w, h, xrel, yrel, display
                self.workspaces[d].append(Window(*((win,) + geom + (screen,))))

    # update workspace list
    def update_workspaces(self):
        self.workspaces = [[] for i in xrange(xlib.get_number_of_desktops(self.display))]
        # normally should be 0 (always active workspace)
        self.current = xlib.get_current_desktop(self.display)

    # update displays
    def update_screens(self):
        self.screens = Screen.get_screens(self.display)

    # swap whole workspaces
    def swap_workspace(self, a, b):
        self.update()

        for win in self.workspaces[a]:
            xlib.set_desktop(self.display, win.id, b)
        for win in self.workspaces[b]:
            xlib.set_desktop(self.display, win.id, a)

        xlib.commit(self.display)

    # swap windows on current displays - implemented for 2 horizontal displays
    def swap(self):
        self.update()

        if len(self.screens) != 2: # unsupported
            return
        if self.screens[0].x == self.screens[1].x: # same offset
            return

        for win in self.workspaces[self.current]:
            i = win.d
            relx = win.x - self.screens[i].x
            rely = win.y - self.screens[i].y
            x = self.screens[(i+1) % 2].x + relx - (2*win.xrel)
            y = self.screens[(i+1) % 2].y + rely - (2*win.yrel)
            xlib.moveresize(self.display, win.id, x, y)

        xlib.commit(self.display)

    # swap workspace on display i - implemented for 2 horizontal displays
    def switch(self, i, target):
        self.update()

        if i>0 and len(self.screens) != 2: # unsupported
            return
        elif i>0 and self.screens[0].x == self.screens[1].x: # same offset
            return

        if target == self.loaded[i]:
            if self.history[i] != None: # swap back to previous workspace
                target = self.history[i]
                self.history[i] = self.loaded[i]
            else: # nowhere to switch, it's already loaded
                return
        else: # just update history
            self.history[i] = self.loaded[i]

        # save active workspace
        for win in self.workspaces[0]:
            if win.d == i:
                xlib.set_desktop(self.display, win.id, self.loaded[i])

        # load target workspace
        for win in self.workspaces[target]:
            if win.d == i:
                xlib.set_desktop(self.display, win.id, 0)

        self.loaded[i] = target
        xlib.commit(self.display)

    # swap winddows between arbitrary independent workspaces
    def swap_displays(self, d1, w1, d2, w2):
        if d1==d2 and w1==w2:
            return

        self.update()

        if len(self.screens) != 2: # unsupported
            return
        if self.screens[0].x == self.screens[1].x: # same offset
            return

        for win in self.workspaces[w1]:
            if win.d == d1:
                xlib.set_desktop(self.display, win.id, w2)
                # move window, we changed displays
                if d1 != d2:
                    relx = win.x - self.screens[d1].x
                    rely = win.y - self.screens[d1].y
                    x = self.screens[d2].x + relx - (2*win.xrel)
                    y = self.screens[d2].y + rely - (2*win.yrel)

                    xlib.moveresize(self.display, win.id, x, y)
        for win in self.workspaces[w2]:
            if win.d == d2:
                xlib.set_desktop(self.display, win.id, w1)
                # move window, we changed displays
                if d1 != d2:
                    relx = win.x - self.screens[d2].x
                    rely = win.y - self.screens[d2].y
                    x = self.screens[d1].x + relx - (2*win.xrel)
                    y = self.screens[d1].y + rely - (2*win.yrel)

                    xlib.moveresize(self.display, win.id, x, y)

        xlib.commit(self.display)

    def command(self, cmd):
        if cmd[0] == 'switch':
            # switch to workspace cmd[2] on display cmd[1]
            if args.length == 3:
                self.switch(cmd[1].to_i, cmd[2].to_i)
        elif cmd[0] == 'swap':
            # swap current halves
            self.swap()
        elif cmd[0] == 'swap_displays':
            # swap any combination of halves
            if len(cmd) == 5:
                try:
                    d1, w1, d2, w2 = int(cmd[1]),int(cmd[2]), int(cmd[3]), int(cmd[4])
                except ValueError:
                    return

                self.swap_displays(d1, w1, d2, w2)
        elif cmd[0] == 'swap_workspace':
            # swap full workspaces
            if len(cmd) == 3:
                try:
                    a, b = int(cmd[1]),int(cmd[2])
                except ValueError:
                    return
                self.swap_workspace(a, b)
        elif cmd[0] == 'set_loaded':
            if len(cmd) == 3:
                try:
                    a, b = int(cmd[1]),int(cmd[2])
                except ValueError:
                    return
                self.set_loaded(a, b)


if __name__ == "__main__":
    m = Manager(display.Display())
    m.update()
    print m.workspaces
    #m.swap_workspace(0,1)
    #m.swap()
    #m.swap_displays(1,1, 0,3)
    #m.switch(1, 2)
