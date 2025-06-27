import ctypes
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

_file = 'pylib.so'
_mod = ctypes.cdll.LoadLibrary(str(BASE_DIR / _file))

cycle = _mod.cycle
cycle.argtypes = (ctypes.c_longlong, )
cycle.restype = ctypes.c_longlong


print(str(BASE_DIR / _file))
ctimer = time.perf_counter()
print(cycle(10000000000))
print(f'Время выполнения цикла на C: {time.perf_counter() - ctimer}')

print('*' * 100)

def count_by_for(n):
    for i in range(n + 1):
        pass
    print(f'i: {i + 18}')

pytimer = time.perf_counter()
# count_by_for(10000000000)
print(f'Время выполнения цикла на Python: {time.perf_counter() - pytimer}')


if __name__ == '__main__':
    pass