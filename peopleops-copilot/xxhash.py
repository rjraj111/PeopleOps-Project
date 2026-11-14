import hashlib

class _H:
    def __init__(self, d=b"", seed=0, size=8):
        self._size = size
        self._h = hashlib.blake2b(d if isinstance(d, bytes) else str(d).encode(), digest_size=size)

    def update(self, d):
        self._h.update(d if isinstance(d, bytes) else str(d).encode())

    def digest(self):
        return self._h.digest()

    def hexdigest(self):
        return self._h.hexdigest()

    def intdigest(self):
        return int.from_bytes(self._h.digest(), "big")

def xxh32(d=b"", seed=0): return _H(d, seed, 4)
def xxh64(d=b"", seed=0): return _H(d, seed, 8)
def xxh3_64(d=b"", seed=0): return _H(d, seed, 8)
def xxh128(d=b"", seed=0): return _H(d, seed, 16)
def xxh3_128(d=b"", seed=0): return _H(d, seed, 16)

def xxh32_hexdigest(d=b"", seed=0): return xxh32(d, seed).hexdigest()
def xxh64_hexdigest(d=b"", seed=0): return xxh64(d, seed).hexdigest()
def xxh3_64_hexdigest(d=b"", seed=0): return xxh3_64(d, seed).hexdigest()
def xxh128_hexdigest(d=b"", seed=0): return xxh128(d, seed).hexdigest()
def xxh3_128_hexdigest(d=b"", seed=0): return xxh3_128(d, seed).hexdigest()

def xxh32_intdigest(d=b"", seed=0): return xxh32(d, seed).intdigest()
def xxh64_intdigest(d=b"", seed=0): return xxh64(d, seed).intdigest()
def xxh3_64_intdigest(d=b"", seed=0): return xxh3_64(d, seed).intdigest()
def xxh128_intdigest(d=b"", seed=0): return xxh128(d, seed).intdigest()
def xxh3_128_intdigest(d=b"", seed=0): return xxh3_128(d, seed).intdigest()