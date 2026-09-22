"""
BSPPLUS 统一身份认证 —— 真实环境联调脚本

只有到能够访问 BSPPLUS_API_ROOT（政务内网，例如 172.29.91.36:9099）的
生产/政务网络环境下，这个脚本才能真正跑通；本地开发环境预期会报连接失败，
这是正常现象，不是脚本的问题。

用途：验证 BSPPLUS /user/login 的真实连通性、请求/响应格式与
《011浪潮政务服务基础服务bspplus对接规范v1.2.docx》3.3.1 的一致性，
不改动、不依赖本系统的业务数据库或业务代码路径——直接复用
app/services/bsp_client.py::BspClient，与正式登录接口走同一份对接逻辑，
联调结果对正式接口同样成立。

安全要求（务必遵守）：
  - 账号通过命令行交互输入；密码必须用 getpass.getpass() 交互输入，
    不接受命令行参数、环境变量、配置文件传入密码。
  - 不打印明文密码、不打印完整 token/refreshToken（BSP 返回的这两个字段
    在 BspClient 里本来就不会被读取/暴露，见 app/services/bsp_client.py）。
  - 只打印经过脱敏的必要字段，用于确认联调是否成功。

执行方式（在能访问 BSPPLUS_API_ROOT 的机器上）：
  cd /app/Enterprise-Service-Center
  BSPPLUS_API_ROOT=http://172.29.91.36:9099 BSPPLUS_APP_CODE=<真实appCode> \\
      .venv/bin/python scripts/bspplus_login_check.py
"""

import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.services.bsp_client import BspAuthFailedException, BspClient, BspServiceException  # noqa: E402


def _mask_middle(value: str | None, head: int = 2, tail: int = 2) -> str:
    if not value:
        return "(空)"
    if len(value) <= head + tail:
        return "*" * len(value)
    tail_part = value[-tail:] if tail > 0 else ""
    return value[:head] + "*" * (len(value) - head - tail) + tail_part


def main() -> int:
    print("=== BSPPLUS /user/login 真实联调检查 ===")
    print(f"BSPPLUS_API_ROOT = {settings.bspplus_api_root or '(未配置)'}")
    print(f"BSPPLUS_APP_CODE = {_mask_middle(settings.bspplus_app_code, head=2, tail=0)}")
    print(f"connect timeout  = {settings.bspplus_connect_timeout_seconds}s")
    print(f"read timeout     = {settings.bspplus_read_timeout_seconds}s")

    if not settings.bspplus_api_root or not settings.bspplus_app_code:
        print("\n[失败] BSPPLUS_API_ROOT / BSPPLUS_APP_CODE 未配置，无法测试。")
        print("请通过环境变量设置后重试，例如：")
        print("  BSPPLUS_API_ROOT=http://172.29.91.36:9099 BSPPLUS_APP_CODE=xxx python scripts/bspplus_login_check.py")
        return 1

    username = input("\n请输入 BSPPLUS 测试账号: ").strip()
    if not username:
        print("[失败] 账号不能为空")
        return 1

    password = getpass.getpass("请输入 BSPPLUS 测试密码（不会回显）: ")
    if not password:
        print("[失败] 密码不能为空")
        return 1

    client = BspClient()
    print("\n正在请求 BSPPLUS /user/login ...")
    try:
        user = client.login(username, password)
    except BspAuthFailedException as exc:
        print(f"\n[认证失败] BSP 判定账号或密码不合法：{exc}")
        print("（说明：连通性正常，接口能正常交互，只是这组账号密码没有通过 BSP 校验）")
        return 2
    except BspServiceException as exc:
        print(f"\n[服务异常] 无法完成本次联调：{exc}")
        print("请确认：网络是否可达 BSPPLUS_API_ROOT、appCode 是否正确、BSP 服务是否正常。")
        return 3

    print("\n[成功] BSPPLUS 认证通过，本地已解析出以下（脱敏后）字段：")
    print(f"  user.id         = {_mask_middle(user.id, head=4, tail=4)}")
    print(f"  user.username   = {user.username}")
    print(f"  user.name       = {user.name}")
    print(f"  user.mobile     = {_mask_middle(user.mobile, head=3, tail=2)}")
    print(f"  user.organCode  = {user.organ_code}")
    print(f"  user.organName  = {user.organ_name}")
    print(f"  user.regionCode = {user.region_code}")
    print(f"  user.regionName = {user.region_name}")
    print("\n（BSP token/refreshToken 本脚本不读取、不展示——本系统登录后使用的是")
    print(" 自己签发的 JWT，不依赖 BSP token 维持会话。）")
    print("\n请把以上字段与 BSPPLUS 后台该账号的真实资料核对，确认字段含义与本系统的")
    print("理解一致（尤其是 user.id 是否确实稳定不变——多次登录同一账号应得到相同的 id）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
