"""MinerU File转Markdown服务的命令行界面。"""

import sys
import argparse

from . import config
from . import server
from .banner import print_banner


def main():
    """命令行界面的入口点。"""
    parser = argparse.ArgumentParser(description="MinerU File转Markdown转换服务")

    parser.add_argument(
        "--output-dir", "-o", type=str, help="保存转换后文件的目录 (默认: ~/mineru-downloads)"
    )

    parser.add_argument(
        "--transport",
        "-t",
        type=str,
        default="stdio",
        help="协议类型 (默认: stdio,可选: sse,streamable-http)",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8001,
        help="服务器端口 (默认: 8001, 仅在使用HTTP协议时有效)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="服务器主机地址 (默认: 0.0.0.0, 仅在使用HTTP协议时有效)",
    )

    args = parser.parse_args()

    # 检查参数有效性
    if args.transport == "stdio" and (args.host != "127.0.0.1" or args.port != 8001):
        print("警告: 在STDIO模式下，--host和--port参数将被忽略", file=sys.stderr)

    # Warn (don't exit) if no API key is configured — per-request keys via ?api_key= are also supported
    if not config.MINERU_TOKEN:
        print(
            "警告: 未设置 MINERU_API_KEY / MINERU_TOKEN 环境变量。\n"
            "可通过 MCP 服务器 URL 中的 ?api_key=YOUR_KEY 参数按请求传入。",
            file=sys.stderr,
        )

    # 如果提供了输出目录，则进行设置
    if args.output_dir:
        server.set_output_dir(args.output_dir)

    # Print startup banner — always to stderr so stdio MCP wire is never touched
    host_display = f"{args.host}:{args.port}" if args.transport in ("sse", "streamable-http") else ""
    print_banner(
        transport=args.transport,
        host=host_display,
        output_dir=server.get_output_dir(),
    )

    server.run_server(mode=args.transport, port=args.port, host=args.host)


if __name__ == "__main__":
    main()
