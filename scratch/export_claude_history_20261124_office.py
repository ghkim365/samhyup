import json
import os
import re

session_path = r'C:\Users\Administrator\.claude\projects\E--Antigravity-builder-samhyup-sales\21ab0f0e-a751-4d8c-8fb7-0a11053faba8.jsonl'
out_md_path = r'E:\Antigravity\builder-samhyup-sales\plan\claude_chat_history_20261124_office.md'
out_html_path = r'E:\Antigravity\builder-samhyup-sales\plan\claude_chat_history_20261124_office.html'

dialogs = []

with open(session_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            d = json.loads(line)
            t = d.get('type')
            ts = d.get('timestamp', '')[:19].replace('T', ' ')
            
            if t == 'user':
                msg = d.get('message', {})
                content = msg.get('content', '')
                if isinstance(content, list):
                    texts = []
                    for c in content:
                        if isinstance(c, dict) and c.get('type') == 'text':
                            texts.append(c.get('text', ''))
                        elif isinstance(c, str):
                            texts.append(c)
                    content = '\n'.join(texts)
                content = re.sub(r'<system-reminder>.*?</system-reminder>', '', content, flags=re.S)
                content = re.sub(r'<system-reminder>.*', '', content, flags=re.S)
                if content and content.strip():
                    # filter out internal CLI noise if any
                    dialogs.append(('User (사용자)', ts, content.strip()))
                    
            elif t == 'assistant':
                msg = d.get('message', {})
                content = msg.get('content', '')
                if isinstance(content, list):
                    texts = []
                    for c in content:
                        if isinstance(c, dict):
                            if c.get('type') == 'text':
                                texts.append(c.get('text', ''))
                        elif isinstance(c, str):
                            texts.append(c)
                    content = '\n\n'.join(texts)
                if content and content.strip():
                    dialogs.append(('Claude Code (Sonnet 5.5)', ts, content.strip()))
        except Exception as e:
            pass

print(f"Extracted {len(dialogs)} messages from Claude session.")

# 1. Write Markdown file
with open(out_md_path, 'w', encoding='utf-8') as f:
    f.write("# 💬 Claude Code 대화 내역 (2026-11-24 · 회사 PC 세션 · 시각은 UTC(한국시간 -9시간))\n\n")
    f.write("> **프로젝트:** `E:\\Antigravity\\builder-samhyup-sales`  \n")
    f.write(f"> **세션 ID:** `21ab0f0e-a751-4d8c-8fb7-0a11053faba8`  \n")
    f.write(f"> **총 대화 턴 수:** {len(dialogs)}회  \n\n")
    f.write("---\n\n")
    
    for speaker, ts, content in dialogs:
        if 'User' in speaker:
            f.write(f"### 👤 {speaker} `[{ts}]`\n\n")
            f.write(f"{content}\n\n")
            f.write("---\n\n")
        else:
            f.write(f"### 🤖 {speaker} `[{ts}]`\n\n")
            f.write(f"{content}\n\n")
            f.write("---\n\n")

print(f"Successfully generated Markdown: {out_md_path}")

# 2. Write Beautiful HTML file for easy reading and Google Docs copy
html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Claude Code 대화 기록 (2026-11-24 · 회사 PC 세션 · 시각은 UTC(한국시간 -9시간))</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Pretendard', 'Malgun Gothic', sans-serif;
      line-height: 1.65;
      color: #1e293b;
      max-width: 900px;
      margin: 40px auto;
      padding: 0 20px;
      background: #f8fafc;
    }}
    .header {{
      background: #ffffff;
      padding: 24px 30px;
      border-radius: 12px;
      border: 1px solid #e2e8f0;
      margin-bottom: 24px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }}
    .msg {{
      margin-bottom: 20px;
      padding: 20px 24px;
      border-radius: 12px;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }}
    .msg-user {{
      background: #f0f7ff;
      border-left: 5px solid #0058be;
    }}
    .msg-claude {{
      background: #ffffff;
      border-left: 5px solid #d97706;
    }}
    .author {{
      font-weight: 700;
      font-size: 15px;
      margin-bottom: 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .time {{
      font-size: 12px;
      color: #94a3b8;
      font-weight: 400;
    }}
    .content {{
      font-size: 14.5px;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    pre, code {{
      background: #0f172a;
      color: #f8fafc;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: Consolas, monospace;
      font-size: 13px;
    }}
    pre {{
      padding: 12px 16px;
      overflow-x: auto;
    }}
  </style>
</head>
<body>
  <div class="header">
    <h1 style="margin: 0 0 10px; font-size: 22px;">💬 Claude Code 대화 내역 (2026-11-24 · 회사 PC 세션 · 시각은 UTC(한국시간 -9시간))</h1>
    <div style="font-size: 13.5px; color: #64748b;">
      프로젝트: <code>E:\\Antigravity\\builder-samhyup-sales</code> | 세션: <code>21ab0f0e-a751-4d8c-8fb7-0a11053faba8</code> | 대화 수: {len(dialogs)}개
    </div>
    <p style="margin: 12px 0 0; font-size: 13px; color: #0058be; font-weight: 600;">
      💡 이 페이지를 브라우저에서 열고 <code>Ctrl+A</code>(전체 선택) ➔ <code>Ctrl+C</code>(복사) 후 구글 독스에 <code>Ctrl+V</code>(붙여넣기)하시면 서식이 깔끔하게 그대로 들어갑니다.
    </p>
  </div>
"""

for speaker, ts, content in dialogs:
    is_user = 'User' in speaker
    cls = 'msg-user' if is_user else 'msg-claude'
    author_color = '#0058be' if is_user else '#b45309'
    icon = '👤' if is_user else '🤖'
    # escape html special chars in content
    safe_content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    html_content += f"""
  <div class="msg {cls}">
    <div class="author" style="color: {author_color};">
      <span>{icon} {speaker}</span>
      <span class="time">{ts}</span>
    </div>
    <div class="content">{safe_content}</div>
  </div>
"""

html_content += """
</body>
</html>
"""

with open(out_html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Successfully generated HTML: {out_html_path}")

