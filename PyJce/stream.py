from typing import Tuple, List
from pyjce.bytebuffer import ByteBuffer
from pyjce.exception import JceDecodeException
from pyjce.struct import JceStruct, JceStructStatics

class HeadData(object):
    tag: int=0
    type: int = 0

    def __init__(self):
        self.tag = 0
        self.type = 0

    def __str__(self):
        return '{tag: %d, type: %d}' % (self.tag, self.type)

    def __repr__(self):
        return '{tag: %d, type: %d}' % (self.tag, self.type)

        
    def clear(self):
        self.tag = 0
        self.type = 0

def read_head(byte_buffer: ByteBuffer) -> Tuple[HeadData, int]:
    head_data = HeadData()
    b = byte_buffer.get()
    head_data.type = b & 0x0F #低4位位类型
    head_data.tag = (b & 0xF0) >> 4 #高4位为tag,
    if head_data.tag != 15: #如果tag为15 则下一个字段为tag
        return (head_data, 1)
    else:
        head_data.tag = byte_buffer.get() & 0xFF
        return (head_data, 2)
        

class JceInputStream(object):
    _bs:ByteBuffer = None
    encoding = 'utf-8'
    
    def __init__(self, bs, i=0):
        self.encoding = 'utf-8'
        if isinstance(bs, ByteBuffer):
            self._bs = bs
        elif isinstance(bs, (bytearray, bytes)):
            self._bs = ByteBuffer(bs)
            self._bs.position = i
        else:
            raise TypeError("'bs' argument must be bytes, bytesarray or ByteBuffer")

    def read_head(self):
        return read_head(self._bs)

    def peak_head(self):
        return read_head(self._bs.duplicate())

    def skip(self, i: int):
        self._bs.position = self._bs.position + i
    
    def skip_to_struct_end(self):
        head_data, _ = self.read_head()
        self.skip_field(head_data.type)
        while (head_data.type != 11):
            head_data, _ = self.read_head()
            self.skip_field(head_data.type)

    def skip_field(self, field_type=None):
        if not field_type:
            head_data, _ = self.read_head()
            field_type = head_data.type
        i = 0
        read_value = None
        if field_type == 0:
            self.skip(1)
        elif field_type == 1:
            self.skip(2)
        elif field_type == 2:
            self.skip(4)
        elif field_type == 3:
            self.skip(8)
        elif field_type == 4:
            self.skip(4)
        elif field_type == 5:
            self.skip(8)
        elif field_type == 6:
            i = self._bs.get()
            if i < 0:
                i += 256
            self.skip(i)
        elif field_type == 7:
            i = self._bs.get_int4()
            self.skip(i)
        elif field_type == 8:
            read_value = self._read_int(0, 0, True)
            while i < read_value * 2:
                self.skip_field()
                i += 1
        elif field_type == 9:
            read_value = self._read_int(0, 0, True)
            while i < read_value:
                self.skip_field()
                i += i
        elif field_type == 10:
            self.skip_to_struct_end()
        elif field_type == 11 or field_type == 12:
            return
        elif field_type == 13:
            head_data,_=self.read_head()
            if head_data.type != 0:
                raise JceDecodeException("skipField with invalid type, type value: " + field_type + ", " + head_data.type)
            i = self._read_int(0, 0, True)
            self.skip(i)
        else:
            raise JceDecodeException("invalid type.")
    
    def skip_to_tag(self, tag: int)->bool:
        try:
            while True:
                head_data, length = self.peak_head()
                if tag > head_data.tag and head_data.type != 0x0B:
                    self.skip(length)
                    self.skip_field(head_data.type)
                else:
                    break
            if head_data.type == 0X0B or tag != head_data.tag:
                return False
            return True
        except (JceDecodeException, BufferError):
            return False

    def re_init(self):
        self.encoding = 'utf-8'
        self._bs.clear()

    def get_tags(self) -> List[int]:
        position = self._bs.position
        # self.re_init()
        tags=[]
        while True:
            try:
                head_data, _ = self.read_head()
                tags.append(head_data.tag)
                self.skip_field(head_data.type)
            except:
                print('exception occured in position: %d, quit' % (self._bs.position))
                break
        self._bs.position = position
        return tags


    def _read_bool(self, b: bool, tag: int, is_require: bool) -> bool:
        c = self._read_int(0, tag, is_require)
        return c != 0

    def _read_int(self, c: int, tag: int, is_require) -> int:
        if self.skip_to_tag(tag):
            head_data, _ = self.read_head()
            if head_data.type == 12:
                c = 0
            elif head_data.type == 0:
                c = self._bs.get()
            elif head_data.type == 1:
                c = self._bs.get_int2()
            elif head_data.type == 2:
                c = self._bs.get_int4()
            elif head_data.type == 3:
                c = self._bs.get_int8()
            else:
                raise JceDecodeException("type mismatch.")
        elif is_require:
            raise JceDecodeException("require field not exist.")
        return c
    
    def _read_float(self, n: float, tag: int, is_require: bool) -> float:
        if self.skip_to_tag(tag):
            head_data, _ = self.read_head()
            if head_data.type == 12:
                n = 0.0
            elif head_data.type == 4:
                n = self._bs.get_float()
            if head_data.type == 5:
                n = self._bs.get_double()
            else:
                raise JceDecodeException("type mismatch.")
        elif is_require:
            raise JceDecodeException("require field not exist.")
        return n
    
    def _read_string(self, s: str, tag: int, is_require: bool) -> str:
        if self.skip_to_tag(tag):
            head_data, _ = self.read_head()
            if head_data.type == 6:
                length = self._bs.get()
                if length < 0:
                    length += 256
                ss = self._bs.get_bytes(length)
                try:
                    s = ss.decode(self.encoding)
                except UnicodeDecodeError:
                    s = ss.decode()
            elif head_data.type == 7:
                length = self._bs.get_int4()
                if length > JceStructStatics.JCE_MAX_STRING_LENGTH or length < 0:
                    raise JceDecodeException("String too long: " + len)
                ss = self._bs.get_bytes(length)
                try:
                    s = ss.decode(self.encoding)
                except UnicodeDecodeError:
                    s = ss.decode()
            else:
                raise JceDecodeException("type mismatch.")
        elif is_require:
            raise JceDecodeException("require field not exist.")
        return s

    def _read_struct(self, o: JceStruct, tag: int, is_require: bool) -> JceStruct:
        ref = None
        if self.skip_to_tag(tag):
            ref = o
            head_data, _ = self.read_head()
            if head_data.type != 10:
                raise JceDecodeException("type mismatch.")
            ref.read_from(self)
            self.skip_to_struct_end()
        elif is_require:
            raise JceDecodeException("require field not exist.")
        return ref

    def _read_list(self, mt, tag: int, is_require: bool) -> list:
        if self.skip_to_tag(tag):
            head_data, _ = self.read_head()
            if head_data.type == 9:
                size = self._read_int(0, 0, True)
                if size < 0:
                    raise JceDecodeException("size invalid: " + size)
                lr = []
                for i in range(size):
                    t = self.read_current(True)
                    lr.append(t)
                return lr
            raise JceDecodeException("type mismatch.")
        elif is_require:
            raise JceDecodeException("require field not exist.")
        return None

    def _read_map(self, m: dict, tag: int, is_require: bool):
        mr = {}
        if self.skip_to_tag(tag):
            head_data, _ = self.read_head()
            if head_data.type == 8:
                size = self._read_int(0, 0, True)
                if size < 0:
                    raise JceDecodeException("size invalid: " + size)
                for i in range(size):
                    k = self.read_current(True)
                    v = self.read_current(True)
                    mr[k] = v
            else:
                raise JceDecodeException("type mismatch.")
        elif is_require:
            raise JceDecodeException("require field not exist.")
        return mr

    def _read_simple_list(self, l, tag: int, is_require: bool):
        lr = b''
        if self.skip_to_tag(tag):
            head_data, _ = self.read_head()
            if head_data.type == 13:
                hh, _ = self.read_head()
                if hh.type != 0:
                    raise JceDecodeException("type mismatch, tag: " + tag + ", type: " + head_data.type + ", " + hh.type)
                size = self._read_int(0, 0, True)
                if size < 0:
                    raise JceDecodeException("invalid size, tag: " + tag + ", type: " + head_data.type + ", " + hh.type + ", size: " + size)
                lr=self._bs.get_bytes(size)
            else:
                raise JceDecodeException("type mismatch.")
        elif is_require:
            raise JceDecodeException("require field not exist.")
        return lr

    def read(self, o, tag: int, is_require: bool):
        if isinstance(o, bool):
            return self._read_bool(o, tag, is_require)
        if isinstance(o, int):
            return self._read_int(o, tag, is_require)
        if isinstance(o, float):
            return self._read_float(o, tag, is_require)
        if isinstance(o, str):
            return self._read_string(o, tag, is_require)
        if isinstance(o, list):
            return self._read_list(o, tag, True)
        if isinstance(o, dict):
            return self._read_map(o, tag, True)
        raise JceDecodeException("read object error: unsupport type.")
    
    def read_current(self, is_require: bool):
        head_data, _ = self.peak_head()
        if head_data.type in (0, 1, 2, 3):
            return self._read_int(0, head_data.tag, is_require)
        elif head_data.type in (4, 5):
            return self._read_float(0.0, head_data.tag, is_require)
        elif head_data.type in (6, 7):
            return self._read_string('', head_data.tag, is_require)
        elif head_data.type == 8:
            return self._read_map({}, head_data.tag, is_require)
        elif head_data.type == 9:
            return self._read_list([], head_data.tag, is_require)
        elif head_data.type == 10:
            return self._read_struct(JceStruct(), head_data.tag, is_require)
        elif head_data.type == 11:
            self.read_head()
            return None
        elif head_data.type == 12:
            self.read_head()
            return 0
        elif head_data.type == 13:
            return self._read_simple_list(b'', head_data.tag, is_require)
        else:
            raise JceDecodeException("read object error: unsupport type.")