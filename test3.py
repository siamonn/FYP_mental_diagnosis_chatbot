import streamlit as st
import json
from datetime import datetime
import time
import os
import dotenv
import re
from openai import OpenAI

dotenv.load_dotenv()
API_KEY = os.getenv("API_KEY")

# Initialize OpenAI client
client = OpenAI(
    base_url='https://xiaoai.plus/v1',
    api_key= API_KEY
)

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ]
)

print(completion)  # 响应
print(completion.choices[0].message)  # 回答