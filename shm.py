# Copyright (C) 2012  Adam Sloboda

from ctypes import *
from ctypes.util import find_library
import six

class SHM:
    # linux/ipc.h or bits/ipc.h
    IPC_CREAT = 0o1000
    IPC_EXCL = 0o2000
    IPC_NOWAIT = 0o2000

    IPC_RMID = 0

    # fn file has to exist
    def __init__(self, fn, proj_id=1, size=4096):
        libcname=find_library("c")
        print('loading C library:', libcname)
        self.libc = CDLL(libcname)

        self.mem = None
        self.fn = fn
        self.proj_id = proj_id

        self.key = self.libc.ftok(fn, proj_id)
        if self.key == -1:
            print('ftok failed for "%s"' % fn)
            self.libc.perror('ftok')
            raise

        self.size = size
        self.create()

    def __str__(self):
        s = string_at(self.mem)
        if six.PY2:
            return s
        else:
            return s.decode('utf-8')

    def write(self, s):
        if not six.PY2:
            s = s.encode('utf-8')
        memmove(self.mem, s, len(s))

    def create(self):
        shmid = self.libc.shmget(self.key, self.size,
                                 0o666 | SHM.IPC_CREAT | SHM.IPC_EXCL)
        if shmid == -1:
            self.libc.perror('shmget1')
            print('key 0x%08x already exists' % self.key)
            shmid = self.libc.shmget(self.key, self.size, 0)

        if shmid == -1:
            self.libc.perror('shmget2')
            print('no shm found')
            raise

        print('shmid = 0x%08x' % shmid)
        self.shmid = shmid

    def attach(self):
        if self.mem:
            self.detach()

        self.libc.shmat.restype=POINTER(c_char)
        mem = self.libc.shmat(self.shmid, None, 0)
        if mem == -1:
            self.libc.perror('shmat')
            raise

        self.mem = mem

    def detach(self):
        if self.libc.shmdt(self.mem) == -1:
            self.libc.perror('shmdt')

    def remove(self):
        return self.libc.shmctl(self.shmid, SHM.IPC_RMID, None)

if __name__ == "__main__":
    s = SHM('/tmp/TEST')
    s.attach()

    import random
    print(s.mem[0])
    s.mem[0] = chr(random.randint(ord('A'), ord('Z')))
    print(s.mem[0])

    memmove(s.mem, 'lala\0', 5)
    print(str(s))

    s.detach()
    s.remove()

    s = SHM('/')
    s.remove()
    #s = SHM('/tmp/TEST2')
