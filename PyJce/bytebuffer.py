import struct

class ByteBuffer(object):
    _bytes = None
    _position = 0
    
    @property
    def bytes(self)->bytes:
        return self._bytes
    
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, value):
        if not isinstance(value, int):
            raise TypeError("'position' attribute must be a integer")
        elif value < 0:
            raise ValueError("'position' attribute must be a positive number")
        elif value > len(self._bytes):
            raise ValueError('')
        else:
            self._position = value

    def __init__(self, bs: bytes):
        if isinstance(bs, bytes):
            self._bytes = bs
        elif isinstance(bs, bytearray):
            self._bytes = bytes(bs)
        else:
            raise TypeError("'bs' argument must be bytes or bytesarray")
    
    def get(self):
        if self._position >= len(self._bytes):
            raise BufferError('reached end of bytes')
        b = self._bytes[self._position]
        self._position += 1
        return b

    def get_bytes(self, size):
        if size < 0:
            raise ValueError("'size' attribute must be a positive number")
        if self._position > len(self._bytes):
            raise BufferError('reached end of bytes')
        if self.position + size > len(self._bytes):
            raise BufferError('reached end of bytes')
        b = self._bytes[self.position:self.position + size]
        self.position = self.position + size
        return b

    def get_int2(self):
        b = self.get_bytes(2)
        return struct.unpack('>h', b)[0]

    def get_int4(self):
        b = self.get_bytes(4)
        return struct.unpack('>i', b)[0]
    
    def get_int8(self):
        b = self.get_bytes(4)
        return struct.unpack('>q', b)[0]

    def get_float(self):
        b = self.get_bytes(4)
        return struct.unpack('>f', b)[0]
    
    def get_double(self):
        b = self.get_bytes(8)
        return struct.unpack('>d', b)[0]
        

    def duplicate(self):
        bb = ByteBuffer(self._bytes)
        bb.position = self.position
        return bb

    def clear(self):
        self._position = 0