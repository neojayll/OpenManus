from tests.sandbox.test_desktop import tell_to_act

if __name__ == "__main__":
    # 示例：通过点击计算器图标打开计算器，然后在计算器中通过点击计算4*2等于几
    prompt = input("目的：")
    tell_to_act(prompt)
