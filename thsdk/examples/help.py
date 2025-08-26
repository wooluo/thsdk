from thsdk import THS
import time

with THS() as ths:

    print("\n=== help doc ===")
    print(ths.help("doc"))
    time.sleep(1)
