import os
import google.generativeai as genai
from dotenv import load_dotenv
import requests
import json
import sys

# Load environment variables (for local dev if .env exists)
load_dotenv()

# --- 天气工具函数定义 (使用免费接口: t.weather.itboy.net) ---
def get_weather_current(location: str):
    """
    获取指定地点的实时天气信息。
    使用 t.weather.itboy.net 接口，需要先查询城市代码。

    Args:
        location (str): 要查询的城市中文名称（例如，"北京"、"上海"）。

    Returns:
        dict: 包含实时天气信息的字典，或者错误信息。
    """
    city_name = location.strip()
    # 移除可能的 "市" 后缀，但如果名字只有两个字且包含市（如"沙市"），可能需要小心，
    # 不过通常城市列表中是 "北京", "朝阳" 等，不带市。
    # 用户输入可能有 "北京市"，列表里是 "北京"。
    if city_name.endswith("市") and len(city_name) > 2:
        city_name = city_name[:-1]
    
    # 1. 加载城市代码
    json_path = os.path.join(os.path.dirname(__file__), 'weather_city.json')
    city_code = None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            city_data = json.load(f)
            
        # 查找城市代码
        found = False
        if "城市代码" in city_data:
            for province in city_data["城市代码"]:
                for city in province.get("市", []):
                    if city.get("市名") == city_name:
                        city_code = city.get("编码")
                        found = True
                        break
                if found:
                    break
        
        if not city_code:
            return {"error": f"未找到城市 '{city_name}' 的代码，请尝试使用标准城市名称（如'北京'而不是'北京市'）。"}

    except FileNotFoundError:
        return {"error": "无法找到城市代码文件 weather_city.json"}
    except json.JSONDecodeError:
        return {"error": "城市代码文件格式错误"}
    except Exception as e:
        return {"error": f"读取城市代码时发生错误: {e}"}

    # 2. 调用天气 API
    url = f"http://t.weather.itboy.net/api/weather/city/{city_code}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # t.weather.itboy.net 响应结构示例:
        # {
        #     "message": "success感谢又拍云(upyun.com)提供CDN赞助",
        #     "status": 200,
        #     "date": "20231205",
        #     "time": "11:00:00",
        #     "cityInfo": {"city": "北京市", "citykey": "101010100", ...},
        #     "data": {
        #         "shidu": "25%",
        #         "pm25": "10.0",
        #         "pm10": "26.0",
        #         "quality": "优",
        #         "wendu": "5",
        #         "ganmao": "极适宜",
        #         "forecast": [
        #             {
        #                 "date": "05",
        #                 "high": "高温 10℃",
        #                 "low": "低温 -3℃",
        #                 "ymd": "2023-12-05",
        #                 "week": "星期二",
        #                 "sunrise": "07:21",
        #                 "sunset": "16:50",
        #                 "aqi": 33,
        #                 "fx": "西南风",
        #                 "fl": "2级",
        #                 "type": "晴",
        #                 "notice": "愿你拥有比阳光明媚的心情"
        #             },
        #             ...
        #         ]
        #     }
        # }

        if data.get('status') == 200:
            weather_data = data.get('data', {})
            forecast_today = weather_data.get('forecast', [{}])[0]
            
            return {
                "location": data.get('cityInfo', {}).get('city', location),
                "condition": forecast_today.get('type'),
                "temperature": weather_data.get('wendu') + "℃", # 实时温度
                "high_temp": forecast_today.get('high'),
                "low_temp": forecast_today.get('low'),
                "wind_direction": forecast_today.get('fx'),
                "wind_power": forecast_today.get('fl'),
                "humidity": weather_data.get('shidu'),
                "air_quality": weather_data.get('quality'),
                "tips": weather_data.get('ganmao') or forecast_today.get('notice'),
                "date": forecast_today.get('ymd'),
                "week": forecast_today.get('week')
            }
        else:
            return {"error": f"查询失败，接口返回状态码: {data.get('status')}, 消息: {data.get('message')}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"请求天气 API 失败: {e}"}
    except json.JSONDecodeError:
        return {"error": "解析 API 响应失败，可能不是有效的JSON。"}
    except Exception as e:
        return {"error": f"发生未知错误: {e}"}

# Gemini API 的 FunctionDeclaration
get_weather_current_tool = genai.protos.FunctionDeclaration(
    name='get_weather_current',
    description='获取指定城市的实时天气信息，包括温度、风向和建议。',
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            'location': genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description='城市名称，例如 "北京"、"武汉"。'
            )
        },
        required=['location']
    )
)
# --- 工具函数定义结束 ---


def run_chat_session_clean(model):
    print(f"\n--- Entering Chat Mode: Memory ON & Tools Enabled ---")
    print("你可以尝试问我天气，例如 '武汉今天天气怎么样？'")
    print("Type 'quit', 'exit', or 'bye' to return to the main menu.")
    print("----------------------------------------------------")

    conversation_history = []

    while True:
        user_input = input(f"\nYou (Tools & History): ").strip()
        if not user_input: continue
        if user_input.lower() in ['quit', 'exit', 'bye']: break

        try:
            # 1. 构建当前轮次的消息列表 (历史 + 当前用户输入)
            current_turn_messages = list(conversation_history) # Copy history
            user_message = {'role': 'user', 'parts': [{'text': user_input}]}
            current_turn_messages.append(user_message)

            # 2. 第一次调用模型
            response = model.generate_content(current_turn_messages, stream=False)

            # 3. 检查是否有工具调用
            tool_call_part = None
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.function_call:
                        tool_call_part = part
                        break
                if tool_call_part: break

            final_response_text = ""

            if tool_call_part:
                # --- 发生了工具调用 ---
                print(f"[系统] 模型请求调用工具: {tool_call_part.function_call.name}")
                
                fn_name = tool_call_part.function_call.name
                fn_args = {k:v for k,v in tool_call_part.function_call.args.items()}
                
                # 执行工具
                tool_result = {}
                if fn_name in globals() and callable(globals()[fn_name]):
                    tool_result = globals()[fn_name](**fn_args)
                    print(f"[系统] 工具执行结果: {tool_result}")
                else:
                    tool_result = {"error": f"Tool '{fn_name}' not found."}

                # 构建工具响应消息
                # 将 "模型请求工具" 的部分加入消息列表
                model_call_message = {'role': 'model', 'parts': [tool_call_part]}
                current_turn_messages.append(model_call_message)
                
                # 将 "工具返回结果" 的部分加入消息列表
                function_response_part = genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=fn_name,
                        response={'result': tool_result} 
                    )
                )
                function_response_message = {'role': 'function', 'parts': [function_response_part]}
                current_turn_messages.append(function_response_message)

                # 再次调用模型获取最终回答
                final_response = model.generate_content(current_turn_messages, stream=False)
                final_response_text = final_response.text
                print(f"Gemini: {final_response_text}")

                # --- 更新长期记忆 ---
                conversation_history.append(user_message)
                conversation_history.append(model_call_message)
                conversation_history.append(function_response_message)
                conversation_history.append({'role': 'model', 'parts': [{'text': final_response_text}]})

            else:
                # --- 普通文本回复 ---
                final_response_text = response.text
                print(f"Gemini: {final_response_text}")
                
                # 更新长期记忆
                conversation_history.append(user_message)
                conversation_history.append({'role': 'model', 'parts': [{'text': final_response_text}]})

        except Exception as e:
            print(f"An error occurred: {e}")
            # import traceback; traceback.print_exc()


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not found.")
        print("Please set it when running the container: -e GEMINI_API_KEY=your_key")
        return

    try:
        genai.configure(api_key=api_key)
        
        preferred_models = ["gemini-2.5-flash"]
        model = None
        active_model_name = None

        print("Initializing Gemini API...")

        # 1. Try preferred models first
        for model_name in preferred_models:
            try:
                # 在这里，我们向模型传入工具定义
                candidate_model = genai.GenerativeModel(model_name, tools=[get_weather_current_tool])
                # 测试调用
                candidate_model.generate_content("test", tools=[get_weather_current_tool], stream=False) 
                model = candidate_model
                active_model_name = model_name
                print(f"Successfully connected to preferred model: {active_model_name}")
                break
            except Exception as e:
                print(f"Failed to connect to {model_name} with tools: {e}")
                continue

        if not model:
             print("Could not connect to preferred model.")
             return

        # 运行同步聊天会话
        run_chat_session_clean(model)

    except Exception as e:
        print(f"Failed to initialize Gemini API: {e}")

if __name__ == "__main__":
    main()