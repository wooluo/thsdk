from thsdk import THS
import pandas as pd
import time


def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_result(title, response, market_info=""):
    """优雅地打印查询结果"""
    print(f"📊 {title}")
    if market_info:
        print(f"   市场范围: {market_info}")
    print(f"   查询状态: {'✅ 成功' if response.success else '❌ 失败'}")
    
    if response.success:
        df = response.df
        if len(df) > 0:
            print(f"   返回结果: {len(df)} 条")
            print(f"   数据列: {', '.join(df.columns.tolist()[:5])}...")
            print("\n   数据预览:")
            # 只显示前3列和前5行，使输出更简洁
            display_df = df.iloc[:5, :5]
            print(f"\n{display_df.to_string(index=False)}\n")
        else:
            print("   ⚠️  未找到匹配的结果\n")
    else:
        print(f"   错误信息: {response.error}\n")


def main():
    ths = THS()
    try:
        # 连接到行情服务器
        print_section("THSDK - 证券模糊查询示例")
        
        response = ths.connect()
        if not response:
            print(f"❌ 连接失败: {response.error}")
            return
        
        print("✅ 成功连接到行情服务器\n")
        
        # =================================================================
        # 示例1: 按名称查询 - 全市场搜索
        # =================================================================
        print_section("示例1: 按名称查询（全市场）")
        response = ths.query_securities("同花顺")
        print_result("查询关键词: '同花顺'", response)
        time.sleep(0.2)
        
        # =================================================================
        # 示例2: 按名称在指定市场查询
        # =================================================================
        print_section("示例2: 按名称查询（限制市场）")
        response = ths.query_securities("同花顺", "SH,SZ")
        print_result("查询关键词: '同花顺'", response, "沪深A股 (SH,SZ)")
        time.sleep(0.2)
        
        # =================================================================
        # 示例3: 国际股票查询
        # =================================================================
        print_section("示例3: 查询国际股票")
        response = ths.query_securities("特斯拉")
        print_result("查询关键词: '特斯拉'", response, "全市场")
        time.sleep(0.2)
        
        # =================================================================
        # 示例4: 美股查询
        # =================================================================
        print_section("示例4: 美股查询（纳斯达克）")
        response = ths.query_securities("特斯拉", "NQ")
        print_result("查询关键词: '特斯拉'", response, "纳斯达克 (NQ)")
        time.sleep(0.2)
        
        # =================================================================
        # 示例5: 指数查询
        # =================================================================
        print_section("示例5: 查询指数")
        response = ths.query_securities("上证指数")
        print_result("查询关键词: '上证指数'", response)
        time.sleep(0.2)
        
        # =================================================================
        # 示例6: 代码查询
        # =================================================================
        print_section("示例6: 按代码查询")
        response = ths.query_securities("600000")
        print_result("查询代码: '600000'", response)
        time.sleep(0.2)

        # =================================================================
        # 示例6: 行业概念查询
        # =================================================================
        print_section("示例7: 按行业概念查询")
        response = ths.query_securities("软件开发","RF")
        print_result("查询行业概念: '软件开发'", response)
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
    
    finally:
        # 断开连接
        ths.disconnect()
        print_section("连接已关闭")
        print("✅ 已成功断开与服务器的连接\n")


if __name__ == "__main__":
    main()
