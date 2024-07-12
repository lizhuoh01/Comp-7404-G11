import re
import torch
from torch import nn
from torch.nn import functional as F
from functools import partial, wraps
from typing import Callable, Optional, List, Union
from transformers import GPT2Tokenizer, GPT2LMHeadModel

# 工具函数
def calculator(expression: str) -> str:
    try:
        result = eval(expression)
        return f"The result of {expression} is {result}."
    except:
        return "Invalid expression"

def qa_system(question: str) -> str:
    answers = {
        "What is the capital of France?": "The capital of France is Paris.",
        "Who is the CEO of OpenAI?": "The CEO of OpenAI is Sam Altman."
    }
    return answers.get(question, "I don't know the answer to that question.")

def search_engine(query: str) -> str:
    results = {
        "OpenAI": "OpenAI is an AI research lab consisting of the for-profit OpenAI LP and its parent company, the non-profit OpenAI Inc.",
        "GPT-3": "GPT-3 is a state-of-the-art language processing AI developed by OpenAI."
    }
    return results.get(query, f"Results for '{query}': Not found.")

def translator(text: str, target_language: str) -> str:
    translations = {
        ("hello", "French"): "bonjour",
        ("world", "Spanish"): "mundo"
    }
    return f"Translated '{text}' to {target_language}: {translations.get((text, target_language), 'translation not available')}."

def calendar(date: str) -> str:
    events = {
        "2024-07-15": "Meeting with the AI team at 10 AM.",
        "2024-12-25": "Christmas Day."
    }
    return f"Events on {date}: {events.get(date, 'No events scheduled.')}"

# 检查值是否存在
def exists(val):
    return val is not None

# 替换函数
def replace_fn(registry: dict[str, Callable], matches, delimiter='→'):
    orig_text = matches.group(0)
    text_without_end_api_token = matches.group(1)
    end_api_token = matches.group(4)
    function_name = matches.group(2)
    if function_name not in registry:
        return orig_text
    fn = registry[function_name]
    params = matches.group(3).split(',')
    params = list(map(lambda s: s.strip(), params))
    params = list(filter(len, params))
    out = try_except(fn, always(None))(*params)
    if not exists(out):
        return orig_text
    return f'{text_without_end_api_token} {delimiter} {str(out)} {end_api_token}'

def try_except(fn, callback=lambda x: x):
    def inner(*args):
        try:
            return fn(*args)
        except Exception as e:
            return callback(e)
    return inner

def always(val):
    def inner(*args, **kwargs):
        return val
    return inner

def create_function_regex(api_start=' [', api_stop=']'):
    api_start_regex, api_stop_regex = map(re.escape, (api_start, api_stop))
    return rf'({api_start_regex}(\w+)\(([^)]*)\))({api_stop_regex})'

def invoke_tools(registry: dict[str, Callable], text: str, delimiter: str = '→', api_start=' [', api_stop=']') -> str:
    regex = create_function_regex(api_start, api_stop)
    replace_ = partial(replace_fn, registry, delimiter=delimiter)
    return re.sub(regex, replace_, text)

# 示例工具注册表
registry = {
    "calc": calculator,
    "qa": qa_system,
    "search": search_engine,
    "translate": translator,
    "calendar": calendar
}

# 创建工具调用的示例文本
text = """
1. Calculate the sum of 15 and 30: [calc(15 + 30)]
2. What is the event on 2024-07-15? [calendar(2024-07-15)]
3. Translate 'hello' to Spanish: [translate(hello, Spanish)]
4. Search information about 'GPT-3': [search(GPT-3)]
5. Who is the CEO of OpenAI? [qa(Who is the CEO of OpenAI?)]
"""

# 调用工具并替换文本中的占位符
output_text = invoke_tools(registry, text)
print(output_text)
