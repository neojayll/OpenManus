import pyautogui
import base64
from PIL import ImageGrab
import io
from openai import OpenAI
from app.config import config
import time

llm_config = config.llm.get("default")
llm_vision_config = config.llm.get("vision")

client = OpenAI(
    api_key=llm_config.api_key,
    base_url=llm_config.base_url,
)
client_vision = OpenAI(
    api_key=llm_vision_config.api_key,
    base_url=llm_vision_config.base_url,
)

history_vision = []
history = []

tools = [
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "能操作windows使用左键点击桌面的指定位置",
            "parameters": {
                "type": "object",
                "properties": {
                    "xy": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "左键点击的x,y坐标",
                    },
                    "reason": {
                        "type": "string",
                        "description": "解释这次左键点击的意图",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "doubleClick",
            "description": "能操作windows使用左键双击桌面的指定位置",
            "parameters": {
                "type": "object",
                "properties": {
                    "xy": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "左键双击的x,y坐标",
                    },
                    "reason": {
                        "type": "string",
                        "description": "解释这次左键双击的意图",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rightClick",
            "description": "能操作windows使用右键点击桌面的指定位置",
            "parameters": {
                "type": "object",
                "properties": {
                    "xy": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "右键点击的x,y坐标",
                    },
                    "reason": {
                        "type": "string",
                        "description": "解释这次右键点击的意图",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "typewrite",
            "description": "能操作windows点击指定位置然后输入字符串",
            "parameters": {
                "type": "object",
                "properties": {
                    "xy": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "点击的x,y坐标",
                    },
                    "text": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "点击后输入的字符串",
                    },
                    "reason": {
                        "type": "string",
                        "description": "解释这次输入的意图",
                    },
                },
            },
        },
    },
]


def tell_to_act(text):
    screenshotWidth, screenshotHeight = ImageGrab.grab().size
    history.append(
        {
            "role": "system",
            "content": f"""
                       你是一个工具调用助手，请提取用户回答中的操作，并根据操作使用对应的function。
                       """,
        }
    )
    history_vision.append(
        {
            "role": "system",
            "content": f"""
                       你是一个远程桌面助手，你将根据我传给你的{screenshotWidth}*{screenshotHeight}分辨率的桌面截图中的内容，使用合适的操作去达成目的。
                       每次你只可以使用一次操作（你能用的操作只有：鼠标单击、鼠标右键单击、鼠标双击、鼠标单击后输入字符串），你在告诉我操作时必须告诉我操作时的坐标（坐标以截图的左上角为原点（0，0）），操作之后我会把新的截图给你，然后你再根据新的截图中的内容判断目的是否达成，如果没有达成则继续操作。
                       请不要关闭visual studio code，屏幕右下角是显示桌面按钮，左下角是开始菜单栏。
                       如果目的达成，请回答：目的达成。
                       """,
        }
    )
    history_vision.append({"role": "user", "content": f"目的：{text}"})
    for i in range(10):
        nmsg = {
            "role": "user",
            "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{capture_and_convert_to_base64()}"}}, {"type": "text", "text": "这是当前界面的截图，请继续你的操作"}],
        }
        history_vision.append(nmsg)
        response1 = client_vision.chat.completions.create(model=llm_vision_config.model, messages=history_vision)
        choose_message = response1.choices[0]
        print(choose_message.message.content)
        if "目的达成" in choose_message.message.content:
            print("#完成#")
            break
        history_vision.append(choose_message.message)
        history.append({"role": "user", "content": choose_message.message.content, "tools": tools})
        response2 = client.chat.completions.create(model=llm_config.model, messages=history, tools=tools)
        if response2.choices[0].message.tool_calls is not None:
            tool_call = response2.choices[0].message.tool_calls[0]
            args_dict = eval(tool_call.function.arguments)
            x = args_dict["xy"][0]
            y = args_dict["xy"][1]
            if x <= 0:
                x = 1
            if y <= 0:
                y = 1
            if x >= screenshotWidth:
                x = screenshotWidth - 1
            if y >= screenshotHeight:
                y = screenshotHeight - 1
            if tool_call.function.name == "click":
                click(x, y)
            elif tool_call.function.name == "rightClick":
                rightClick(x, y)
            elif tool_call.function.name == "doubleClick":
                doubleClick(x, y)
            elif tool_call.function.name == "typewrite":
                doubleClick(x, y, args_dict["text"])
        print(response2.choices[0].message)
        with open("1.log", "a") as log_file:
            log_file.write(choose_message.message.content + "\n")


def click(x, y):
    pyautogui.moveTo(x, y, duration=1)
    pyautogui.click()
    time.sleep(2)


def rightClick(x, y):
    pyautogui.moveTo(x, y, duration=1)
    pyautogui.rightClick()
    time.sleep(2)


def doubleClick(x, y):
    pyautogui.moveTo(x, y, duration=1)
    pyautogui.doubleClick()
    time.sleep(2)


def typewrite(x, y, text):
    click(x, y)
    pyautogui.typewrite(text)
    time.sleep(2)


def capture_and_convert_to_base64():
    """
    截屏当前桌面
    """
    screenshot = ImageGrab.grab()
    screenshot_bytes = io.BytesIO()
    screenshot.save(screenshot_bytes, format="PNG")
    screenshot_bytes.seek(0)
    base64_image = base64.b64encode(screenshot_bytes.getvalue()).decode("utf-8")
    return base64_image


if __name__ == "__main__":
    prompt = input("目的：")
    tell_to_act(prompt)
