# Copyright (C) 2012  Adam Sloboda

from Xlib import display, error
from screen import Screen
import xlib
from time import sleep
from shm import SHM
import os

# TODO why are reported values +10 and +46?
# x = 10 = 2x5 = 5 is w of window border
# y = 46 = 2x23 = 23 is h of window title bar
# (both reported as .x/.y geometry, is this correct?)

class Window:
    def __init__(self,win,x,y,w,h,xrel,yrel,display):
        self.id = win
        self.x, self.y, self.w, self.h, self.xrel, self.yrel = x,y,w,h,xrel,yrel
        self.d = display

# automatically growing list
class AutoList(list):
    def __init__(self, item=None):
        super(AutoList, self).__init__()
        self.item = item
        self.callable = callable(item)

    def __getitem__(self, i):
        if i >= len(self):
            if self.callable:
                self.__setitem__(i, self.item())
                return self[i]
            else:
                return self.item
        else:
            return super(AutoList, self).__getitem__(i)

    def __setitem__(self, i, value):
        if i >= len(self):
            for j in xrange(len(self), i):
                if self.callable:
                    self.append(self.item())
                else:
                    self.append(self.item)
            self.append(value)
        else:
            super(AutoList, self).__setitem__(i, value)

    def trunc(self, n):
        for i in xrange(n, len(self)):
            self.pop()

class Manager(object):
    def __init__(self, display, store=None, proj_id=1):
        self.display = display

        # windows will be moved to workspace 0 when switching
        self.init_loaded()
        # previous loaded workspaces
        self.history = AutoList()
        # window focuses for each [display][workspace]
        self.focus = AutoList(AutoList)

        if store:
            self.store = SHM(store, proj_id=proj_id)
            self.store.create()
            self.store.attach()
            self.load()
        else:
            self.store = None

    def init_loaded(self):
        self.loaded = AutoList(1)

    def save(self):
        if self.store:
            s = '%s\n%s\0' % (str(self.loaded), str(self.focus))
            self.store.write(s)

    def load(self):
        if not self.store:
            return

        state = str(self.store).splitlines()
        if len(state) != 2:
            self.store.write('\0')
            print 'wiping invalid state %s' % state
            return

        print 'loading:\n', state
        try:
            parsed = eval(state[0])
            # copy items
            for i in parsed:
                self.loaded.append(i)
            print 'loaded = ', self.loaded
        except:
            self.store.write('\0')
            raise

        try:
            parsed = eval(state[1])
            # copy items
            for i in xrange(len(parsed)):
                for j in xrange(len(parsed[i])):
                    if parsed[i][j]:
                        self.focus[i][j] = parsed[i][j]

            print 'focus = ', self.focus
        except:
            self.store.write('\0')
            raise

    # load current WM state
    def update(self):
        self.update_screens()
        self.update_workspaces()
        self.update_windows()

    # set arbitrary state for loaded desktop
    def set_loaded(self, loaded):
        self.init_loaded()
        for i in xrange(len(loaded)):
            self.loaded[i] = loaded[i]
        self.save()

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
            try:
                d = xlib.get_desktop(self.display, win)
            except error.BadWindow:
                # crashes in create_resource_object.get_full_property sometimes
                continue
            if d != 0xffffffff:
                geom = xlib.get_geometry(self.display, win)
                screen = self.get_screen(geom[0])
                # win_id, x, y, w, h, xrel, yrel, display
                self.workspaces[d].append(Window(*((win,) + geom + (screen,))))

    # update workspace list
    def update_workspaces(self):
        self.workspaces = AutoList(AutoList)
        # normally should be 0 (always active workspace)
        self.current = xlib.get_current_desktop(self.display)

    # update displays
    def update_screens(self):
        self.screens = Screen.get_screens(self.display)
        num = len(self.screens)
        if num < len(self.loaded):
            self.loaded.trunc(num)
            self.history.trunc(num)

    # swap whole workspaces
    def swap_workspace(self, a, b):
        self.update()

        for win in self.workspaces[a]:
            xlib.set_desktop(self.display, win.id, b)
        for win in self.workspaces[b]:
            xlib.set_desktop(self.display, win.id, a)

        self.display.sync()

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

        self.display.sync()

    # swap workspace on display i - implemented for 2 horizontal displays
    def switch(self, i, target):
        # we have to be on workspace 0 or else it's confusing to user
        if xlib.get_current_desktop(self.display) != 0:
            # TODO maybe switch to workspace 0?  it might be confusing too
            #xlib.set_current_desktop(self.display, 0)
            return

        self.update()

        if i>0 and len(self.screens) != 2: # unsupported
            return
        elif i>0 and self.screens[0].x == self.screens[1].x: # same offset
            return

        # save focus
        win = xlib.get_active_window(self.display)
        try:
            if xlib.get_desktop(self.display, win) == 0:
                # this rules out 0xffffffff
                self.focus[i][self.loaded[i]] = win
        except error.BadWindow:
            pass

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
        self.display.sync()

        self.save()

        # load focus
        win = self.focus[i][target]
        if win:
            # we have to wait for the windows to be moved
            sleep(0.01)
            xlib.set_active_window(self.display, win)
            self.display.sync()

    # swap winddows between arbitrary independent workspaces
    def swap_displays(self, d1, w1, d2, w2):
        if d1==d2 and w1==w2:
            return

        self.update()

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

        self.display.sync()

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

class Manager0(Manager):
    # because of self.loaded behaviour we need another SHM (proj_id=2)
    def __init__(self, display, store=None, proj_id=2):
        super(Manager0, self).__init__(display, store, proj_id)

    def init_loaded(self):
        self.loaded = AutoList(0)

    # alternative version - uses only half (index 0)
    # swap workspace on display i
    def switch(self, i, target):
        # we have to be on workspace 0 or else it's confusing to user
        if xlib.get_current_desktop(self.display) != 0:
            xlib.set_current_desktop(self.display, 0)

        self.update()

        # are we trying to switch non-existing screen?
        if i >= len(self.screens):
            return

        # TODO should work for more displays, i can't test it
        # TODO even with mirrored if get_screens leaves them out
        if i>0:
            # screens are sorted by x, this will return if there is mirrored
            for j in xrange(1, len(self.screens)):
                if self.screens[j-1].x == self.screens[j].x: # same offset
                    return

        # save focus
        win = xlib.get_active_window(self.display)
        try:
            if xlib.get_desktop(self.display, win) == 0:
                # this rules out 0xffffffff
                self.focus[0][self.loaded[i]] = win
        except error.BadWindow:
            pass

        if target == self.loaded[i]:
            if self.history[i] != None: # swap back to previous workspace
                target = self.history[i]
                self.history[i] = self.loaded[i]
            else: # nowhere to switch, it's already loaded
                return
        else: # just update history
            # if we still have initial value, ignore
            if self.loaded[i] != 0:
                self.history[i] = self.loaded[i]

        try:
            # already loaded elsewhere (it can't be us)
            where = self.loaded.index(target)
            # don't do just swap(), swap arbitrary display numbers
            self.swap_displays(i, 0, where, 0)
            self.loaded[where] = self.loaded[i]
            self.loaded[i] = target
            return
        except ValueError:
            # continue
            pass

        # save (we use whole workspace on display 0 for storing windows)
        for win in self.workspaces[0]:
            if win.d == i:
                xlib.set_desktop(self.display, win.id, self.loaded[i])
                # move window, we changed displays
                if win.d != 0:
                    relx = win.x - self.screens[i].x
                    rely = win.y - self.screens[i].y
                    x = self.screens[0].x + relx - (2*win.xrel)
                    y = self.screens[0].y + rely - (2*win.yrel)

                    xlib.moveresize(self.display, win.id, x, y)

        # load workspace
        for win in self.workspaces[target]:
            # we are using screen 0, ignore windows outside
            if win.d == 0:
                xlib.set_desktop(self.display, win.id, 0)
                # move window, we changed displays
                if win.d != i:
                    relx = win.x - self.screens[0].x
                    rely = win.y - self.screens[0].y
                    x = self.screens[i].x + relx - (2*win.xrel)
                    y = self.screens[i].y + rely - (2*win.yrel)

                    xlib.moveresize(self.display, win.id, x, y)

        self.loaded[i] = target
        self.display.sync()

        self.save()

        # load focus
        win = self.focus[i][target]
        if win:
            # we have to wait for the windows to be moved
            sleep(0.01)
            xlib.set_active_window(self.display, win)
            self.display.sync()
            # sometimes it fails, again
            sleep(0.2)
            xlib.set_active_window(self.display, win)
            self.display.sync()

if __name__ == "__main__":
    m = Manager(display.Display())
    m.update()
    print m.workspaces
    m = Manager(display.Display(), store='/')
    print m.focus[3]
    print m.focus
    print m.history[3]
    print m.loaded[3]
    m = Manager0(display.Display(), store='/')
    print m.focus[3]
    print m.focus
    print m.history[3]
    print m.loaded[3]

    #m.swap_workspace(0,1)
    #m.swap()
    #m.swap_displays(1,1, 0,3)
    #m.switch(1, 2)

