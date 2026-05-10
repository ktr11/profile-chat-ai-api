from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))


def invoke_chat(history: list[dict], user_message: str) -> str:
    # TODO: LangChain + ChatAnthropic に差し替える
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    return f"[stub] {now} に受信: 「{user_message}」（履歴 {len(history)} 件）"
