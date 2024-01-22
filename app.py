import streamlit as st
from streamlit_chat import message
import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv,find_dotenv

load_dotenv(find_dotenv())
weather_api_key = os.getenv("WEATHER_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
st.set_page_config(page_title="Shakeel")
st.header("Function Calling Chatbot")
    
def main():
    
    user_input = st.chat_input("Ask Question")
    if user_input:
        second_response = run_conversation(user_input)
        message(user_input,is_user=True)
        message(second_response)




# get current weather condition
def get_current_weather(location,unit="farenheit"):
    try:
        location_response = requests.get(f"http://dataservice.accuweather.com/locations/v1/cities/search?apikey={weather_api_key}&q={location}")
        if location_response.status_code == 200:
            lacation_data = location_response.json()
            location_key = lacation_data[0]["Key"]
            current_weather_condition = requests.get(f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}?apikey={weather_api_key}&language=en-us&details=True")
            if current_weather_condition.status_code == 200:
                current_weather_data = current_weather_condition.json()
                data = current_weather_data[0]
                return json.dumps(data,indent=2)
    except Exception as e:
        st.write(f"Error : {e}")        
            
        
def run_conversation(user_input):
        messages = [{"role":"user","content":user_input}]
        tools = [
            {
                "type":"function",
                "function": {
                    "name":"get_current_weather",
                    "description":"Get the current weather for given location",
                    "parameters":{
                        "type":"object",
                        "properties":{
                            "location":{
                                "type":"string",
                                "description":"cities of Pakistan"    
                            },
                            "unit":{"type":"string","enum":["celsius","farenheit"]},
                        },
                    },  "required":["location"]
                },
            }
        ]
            
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=messages,
            tools=tools,
        )
        response_messages = response.choices[0].message
        tool_calls = response_messages.tool_calls
        if tool_calls:
            available_functions = {
                "get_current_weather":get_current_weather,
            }
            
            messages.append(response_messages)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(
                    location = function_args.get("location"),
                    unit = function_args.get("unit")

                )
                messages.append(
                    {
                        "tool_call_id":tool_call.id,
                        "role":"tool",
                        "content":function_response, 
                    }
                )
            second_response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=messages,
            )
            response_message = second_response.choices[0].message.content
            return response_message
if __name__ == "__main__":
    main()    