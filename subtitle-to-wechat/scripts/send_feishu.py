#!/usr/bin/env python3
"""Send article summary to Feishu group bot webhook."""

import argparse
import json
import urllib.request

DEFAULT_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/a91e9058-32c8-4232-91b8-5620af17aa87"


def send_to_feishu(title: str, key_points: list[str], webhook: str = DEFAULT_WEBHOOK) -> dict:
    content = [[{"tag": "text", "text": title, "style": ["bold"]}]]
    content.append([{"tag": "text", "text": "\n📋 要点摘录："}])
    for i, point in enumerate(key_points[:5], 1):
        content.append([{"tag": "text", "text": f"\n{i}. {point}"}])
    content.append([{"tag": "text", "text": "\n\n✅ 完整文稿已生成，请查看文档。"}])

    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "📝 新文稿编译完成",
                    "content": content,
                }
            }
        },
    }

    req = urllib.request.Request(
        webhook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main() -> None:
    parser = argparse.ArgumentParser(description="Push subtitle-to-wechat summary to Feishu.")
    parser.add_argument("--title", required=True, help="Article title")
    parser.add_argument(
        "--points",
        required=True,
        help="JSON array of key points, e.g. '[\"p1\",\"p2\"]'",
    )
    parser.add_argument("--webhook", default=DEFAULT_WEBHOOK, help="Feishu webhook URL")
    args = parser.parse_args()

    key_points = json.loads(args.points)
    if not isinstance(key_points, list):
        raise ValueError("--points must be a JSON array")

    result = send_to_feishu(args.title, [str(p) for p in key_points], webhook=args.webhook)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
