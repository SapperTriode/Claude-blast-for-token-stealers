"""
交互式对话脚本，连接 dummy_model 蜜罐服务，观察随机输出。
用法: python3.12 chat.py [base_url]
"""

import json
import sys
import urllib.request

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
URL = f"{BASE_URL}/v1/messages"


def stream_chat(messages: list[dict], model: str = "claude-3-5-sonnet-20241022"):
    """流式请求，逐事件打印 SSE 内容"""
    body = json.dumps({
        "model": model,
        "max_tokens": 256,
        "stream": True,
        "messages": messages,
    }).encode()

    req = urllib.request.Request(
        URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": "test",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        event_type = ""
        for raw_line in resp:
            line = raw_line.decode("utf-8").rstrip("\n")
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])

                if event_type == "message_start":
                    msg = data["message"]
                    print(f"\033[2m[{msg['id']} | model={msg['model']} | input_tokens={msg['usage']['input_tokens']}]\033[0m")

                elif event_type == "content_block_start":
                    block = data["content_block"]
                    if block["type"] == "thinking":
                        print("\033[36m[thinking] \033[0m", end="", flush=True)
                    else:
                        print("\033[32m", end="", flush=True)

                elif event_type == "content_block_delta":
                    delta = data["delta"]
                    if delta["type"] == "thinking_delta":
                        print(delta["thinking"], end="", flush=True)
                    elif delta["type"] == "text_delta":
                        print(delta["text"], end="", flush=True)
                    elif delta["type"] == "signature_delta":
                        print(f"\033[2m[sig]\033[0m", end="", flush=True)

                elif event_type == "content_block_stop":
                    print("\033[0m")

                elif event_type == "message_delta":
                    usage = data["usage"]
                    print(f"\033[2m[stop_reason={data['delta']['stop_reason']} | output_tokens={usage['output_tokens']}]\033[0m")

                elif event_type == "message_stop":
                    pass


def main():
    messages: list[dict] = []
    print("dummy_model 交互对话 (输入 quit 退出, clear 清空历史)")
    print("-" * 50)

    while True:
        try:
            user_input = input("\n\033[1mYou:\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("再见!")
            break
        if user_input.lower() == "clear":
            messages.clear()
            print("历史已清空")
            continue

        messages.append({"role": "user", "content": user_input})

        print("\n\033[1mDummy:\033[0m")
        try:
            stream_chat(messages)
        except Exception as e:
            print(f"\n\033[31m请求失败: {e}\033[0m")


if __name__ == "__main__":
    main()
