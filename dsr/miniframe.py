class PayloadTooLargeError(Exception):
    pass

def computeCRC_8(data, pattern = '0xD5'):
    div = 256 + int(pattern, 16)
    x = 0
    for c in data:
        x = (x<<8) + ord(c)
        for i in [7,6,5,4,3,2,1,0]:
            if x >> (i+8):
                x ^= div << i
        assert x < div
    return x

class MiniFrame:
    @classmethod
    def unpack(self,packed):
        length = ord(packed[0])
        content = packed[2:2+length]


        frame = MiniFrame(packed[1],content)
        frame.valid = packed[2+length] == chr(computeCRC_8(packed[0:2+length]))


        return frame

    def __init__(self,frameType,payload):
        self._payload = payload
        self._frameType = frameType

    def pack(self):
        l = len(self._payload)

        if l > 255:
            raise PayloadTooLargeError('Payload of length %d is too long, maximum is 255' % l)

        bytes = chr(l) + self._frameType + self._payload
        bytes += chr(computeCRC_8(bytes))


        return bytes

    @property
    def payload(self):
        return self._payload

    @property
    def frameType(self):
        return self._frameType
