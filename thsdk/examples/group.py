import time

from thsdk import THS
import pandas as pd

# cookie直接在浏览器辅助，格式例如:
# cookie = "_ga=xxx; searchGuide=xxx; _clck=xxx; u_ukey=xxx; u_uver=xxx; u_dpass=xxx; u_did=xxx; u_ttype=xxx; userid=xxx; u_name=xxx; escapename=xxx; user_status=xxx; user=xxx; ticket=xxx; utk=xxx; v=xxx;"

cookie = ""
if cookie == "":
    raise ValueError("Cookie未设置，请先配置Cookie后再运行程序。")

with THS() as ths:
    print("\n获取分组数据:")
    response = ths.group(cookie)
    if not response.is_success():
        print(f"错误信息: {response.err_info}")

    result = response.get_result()

    version = result.get("version", "N/A")

    print("verion:", version)

    if 'group_list' in result:
        group_list = result['group_list']
        if isinstance(group_list, list):
            for group in group_list:
                if isinstance(group, dict):
                    group_id = group.get('id', "N/A")
                    group_name = group.get('name', "N/A")
                    print("id:", group_id, "name:", group_name, "body:", group)
        else:
            print("'group_list' is not a list.")
    else:
        print("Fields 'group_list' not found in the response or invalid format.")

    time.sleep(1)

    group_name1 = "测试"
    group_name2 = "测试2"

    names = []
    if 'group_list' in result:
        group_list = result['group_list']
        if isinstance(group_list, list):
            names = [group.get('name') for group in group_list if isinstance(group, dict) and 'name' in group]
        else:
            print("'group_list' is not a list.")
    else:
        print("Fields 'group_list' not found in the response or invalid format.")

    group_names = [group_name1, group_name2]
    for group_name in group_names:
        print("\n创建新分组:", group_name)
        if group_name in names:
            print(f"Group name '{group_name}' 已存在")
        else:
            response = ths.group_new(cookie, group_name=group_name, version=version)
            if not response.is_success():
                print(f"创建分组失败,错误信息: {response.err_info}")
            else:
                print("创建分组成功")
            result = response.get_result()
            print(response)
            if 'version' in result:
                version = result["version"]
                print("新增分组成功 更新version:", version)
        time.sleep(1)

    print("\n删除分组:", group_name2)
    response = ths.group(cookie)
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    result = response.get_result()

    target_del_id = ""
    if 'group_list' in result:
        for group in result['group_list']:
            if group.get('name') == group_name2:
                target_del_id = group.get('id', "")
                break

    print("删除目标id:", target_del_id)
    if not target_del_id == "":
        response = ths.group_delete(cookie, ids=target_del_id, version=version)
        if not response.is_success():
            print(f"删除分组失败,错误信息: {response.err_info}")
        else:
            print("删除分组成功")
        print(response)
        result = response.get_result()
        if 'version' in result:
            version = result["version"]
            print("删除成功 更新version:", version)

    time.sleep(1)

    print("\n添加分组元素:", group_name1)
    response = ths.group(cookie)
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    result = response.get_result()
    target_group_id = ""
    if 'group_list' in result:
        for group in result['group_list']:
            if group.get('name') == group_name1:
                target_group_id = group.get('id', "")
                break
    print("添加目标id:", target_group_id)

    if not target_group_id == "":
        response = ths.group_code_add(cookie, id=target_group_id, ths_codes=["USHA600519", "USZA300033"],
                                      version=version)
        if not response.is_success():
            print(f"添加分组元素失败,错误信息: {response.err_info}")
        else:
            print("添加分组元素成功")
            print(response)
            result = response.get_result()
            if 'version' in result:
                version = result["version"]
                print("添加分组元素成功 更新version:", version)

    time.sleep(1)

    print("\n删除分组元素:", group_name1)
    response = ths.group(cookie)
    if not response.is_success():
        print(f"错误信息: {response.err_info}")
    result = response.get_result()
    target_group_id = ""
    if 'group_list' in result:
        for group in result['group_list']:
            if group.get('name') == group_name1:
                target_group_id = group.get('id', "")
                break
    print("添加目标id:", target_group_id)

    if not target_group_id == "":
        response = ths.group_code_delete(cookie, id=target_group_id, ths_codes=["USHA600519"],
                                         version=version)
        if not response.is_success():
            print(f"删除分组元素失败,错误信息: {response.err_info}")
        else:
            print("删除分组元素成功")
            print(response)
            result = response.get_result()
            if 'version' in result:
                version = result["version"]
                print("删除分组元素成功 更新version:", version)

    time.sleep(1)
