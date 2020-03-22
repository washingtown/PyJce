import json

class JceStructStatics:
    BYTE = 0
    SHORT = 1
    INT = 2
    LONG = 3
    FLOAT = 4
    DOUBLE = 5
    STRING1 = 6
    STRING4 = 7
    MAP = 8
    LIST = 9
    STRUCT_BEGIN = 10
    STRUCT_END = 11
    ZERO_TAG = 12
    SIMPLE_LIST = 13
    JCE_MAX_STRING_LENGTH = 104857600

class JceStruct(object):
    
    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value

    def read_from(self, stream):
        self.data.clear()
        head_data, _ = stream.peak_head()
        while head_data.type != 11 and stream._bs.position < len(stream._bs.bytes):
            tag = head_data.tag
            value = stream.read_current(True)
            if isinstance(value, bytes) and len(value) > 0:
                try:
                    s = JceStruct()
                    from PyJce.stream import JceInputStream
                    s.read_from(JceInputStream(value))
                    self.data[tag] = s
                except:
                    self.data[tag] = value
            else:
                self.data[tag] = value
            if stream._bs.position >= len(stream._bs.bytes):
                break
            head_data, _ = stream.peak_head()
    
    def to_json(self):
        return json.dumps(self,cls=JceStructEnconding,ensure_ascii=False)

class JceStructEnconding(json.JSONEncoder):
    def default(self, o): # pylint: disable=E0202
        if isinstance(o, JceStruct):
            if len(o.data) == 1:
                return list(o.data.values())[0]
            else:
                return o.data
        if isinstance(o, (bytes, bytearray)):
            return str(o)