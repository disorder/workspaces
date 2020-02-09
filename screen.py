# Copyright (C) 2012  Adam Sloboda

from operator import attrgetter

class Screen:
    def __init__(self, w,h,x,y):
        self.w, self.h, self.x, self.y = int(w), int(h), int(x), int(y)

    def __repr__(self):
        return '<Screen: %dx%d at %d,%d>' % (self.w, self.h, self.x, self.y)

    # returns screens sorted by horizontal offset (x)
    @staticmethod
    def get_screens(display):
        screens = []
        for s in display.xinerama_query_screens().screens:
            # hack: i am keeping third (LVDS) on and overlapping, skip
            # without this switching works only for leftmost display
            # (overlap is not handled)
            for i, screen in enumerate(screens):
                if screen.x == s['x']:
                    # keep larger
                    if s['height'] > screen.h:
                        screens[i] = Screen(s['width'], s['height'], s['x'], s['y'])
                    break
            else:
                screens.append(Screen(s['width'], s['height'], s['x'], s['y']))
        return sorted(screens, key=attrgetter('x'))

if __name__ == "__main__":
    from Xlib import display
    print(Screen.get_screens(display.Display()))
