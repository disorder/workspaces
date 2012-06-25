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
            screens.append(Screen(s['width'], s['height'], s['x'], s['y']))
        return sorted(screens, key=attrgetter('x'))

if __name__ == "__main__":
    from Xlib import display
    print Screen.get_screens(display.Display())
