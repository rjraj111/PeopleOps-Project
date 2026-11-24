import msgpack

class MsgpackEncodeError(Exception):
    pass

class MsgpackDecodeError(Exception):
    pass

def __getattr__(name):
    if name.startswith("OPT_"):
        return 0
    raise AttributeError(f"module 'ormsgpack' has no attribute '{name}'")

def packb(obj, default=None, option=0):
    try:
        return msgpack.packb(obj, default=default, use_bin_type=True)
    except Exception as e:
        raise MsgpackEncodeError(str(e))

def unpackb(data, ext_hook=None, option=0):
    try:
        return msgpack.unpackb(data, raw=False, strict_map_key=False, ext_hook=ext_hook)
    except Exception as e:
        raise MsgpackDecodeError(str(e))
