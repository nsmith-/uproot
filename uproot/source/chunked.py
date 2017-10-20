#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import numpy

from uproot.cache.memorycache import MemoryCache

class ChunkedSource(object):
    def __init__(self, path, chunkbytes=8*1024, limitbytes=1024**2):
        self._path = path
        self._chunkbytes = chunkbytes
        if limitbytes is None:
            self._cache = {}
        else:
            self._cache = MemoryCache(limitbytes)
        self._source = None

    def __del__(self):
        self.dismiss()

    def _read(self, chunkindex):
        raise NotImplementedError

    def dismiss(self):
        pass

    def data(self, start, stop):
        assert start >= 0
        assert stop >= 0
        assert stop > start

        chunkstart = start // self._chunkbytes
        if stop % self._chunkbytes == 0:
            chunkstop = stop // self._chunkbytes
        else:
            chunkstop = stop // self._chunkbytes + 1

        out = numpy.empty(stop - start, dtype=numpy.uint8)

        for chunkindex in range(chunkstart, chunkstop):
            try:
                chunk = self._cache[chunkindex]
            except KeyError:
                self._open()
                chunk = self._cache[chunkindex] = self._read(chunkindex)

            cstart = 0
            cstop = self._chunkbytes
            gstart = chunkindex * self._chunkbytes
            gstop = (chunkindex + 1) * self._chunkbytes

            if gstart < start:
                cstart += start - gstart
                gstart += start - gstart
            if gstop > stop:
                cstop -= gstop - stop
                gstop -= gstop - stop

            if cstop - cstart > len(chunk):
                raise IndexError("indexes {0}:{1} are beyond the end of data source {2}".format(gstart + len(chunk), stop, repr(self._path)))

            out[gstart - start : gstop - start] = chunk[cstart : cstop]

        return out
