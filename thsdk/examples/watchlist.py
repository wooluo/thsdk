import time

from thsdk import THS
import pandas as pd

# cookie直接在浏览器获取，格式例如:
# cookie = "_ga=xxx; searchGuide=xxx; _clck=xxx; u_ukey=xxx; u_uver=xxx; u_dpass=xxx; u_did=xxx; u_ttype=xxx; userid=xxx; u_name=xxx; escapename=xxx; user_status=xxx; user=xxx; ticket=xxx; utk=xxx; v=xxx;"

cookie = ""
if cookie == "":
    raise ValueError("Cookie未设置，请先配置Cookie后再运行程序。")

with THS() as ths:
    print("获取自选股列表:")
    response = ths.watchlist(cookie)
    print(pd.DataFrame(response.get_result()))
    time.sleep(1)

    print("添加自选股: 300033")
    response = ths.watchlist_add(cookie, code="300033")
    print(response)
    time.sleep(1)

    print("添加自选股: 600519")
    response = ths.watchlist_add(cookie, code="600519")
    print(response)
    time.sleep(1)

    print("删除自选股: 600519")
    response = ths.watchlist_delete(cookie, code="600519", marketid="17")
    print(response)
    time.sleep(1)
