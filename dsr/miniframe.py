class PayloadTooLargeError(Exception):
    pass

class MiniFrame:
#    @classmethod
    def unpack(payload):
        frame = Frame()
        return frame

    def __init__(self,payload):
        self._payload = payload

    def pack(self):
        l = len(self._payload)
        if l > 255:
            raise PayloadTooLargeError('Payload of length %d is too long, maximum is 255' % l)
