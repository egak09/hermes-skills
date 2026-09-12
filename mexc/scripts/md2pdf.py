#!/usr/bin/env python3
"""Markdown 报告 → HTML → PDF（Chromium headless）
用法：python md2pdf.py <input.md> <output_basename>
"""
import sys, os, re, base64, subprocess
import markdown

CHROME = os.path.expanduser('~/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome')

def img_to_datauri(path):
    ext = os.path.splitext(path)[1].lower().lstrip('.')
    mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'svg': 'image/svg+xml'}.get(ext, 'image/png')
    with open(path, 'rb') as f:
        return f'data:{mime};base64,' + base64.b64encode(f.read()).decode()

def build(md_path, base):
    md_text = open(md_path, encoding='utf-8').read()
    workdir = os.path.dirname(os.path.abspath(md_path))

    # 把 charts/xxx.png 引用内联成 base64（Chromium 本地文件安全限制友好）
    def repl(m):
        alt, rel = m.group(1), m.group(2)
        p = os.path.join(workdir, rel)
        if os.path.exists(p):
            return f'![{alt}]({img_to_datauri(p)})'
        return m.group(0)
    md_text = re.sub(r'!\[([^\]]*)\]\(([^)]+\.(?:png|jpg|jpeg|svg))\)', repl, md_text)

    body = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'sane_lists', 'attr_list'])

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{os.path.basename(md_path)}</title>
<style>
  @page {{ size: A4; margin: 16mm 14mm; }}
  body {{ font-family: "WenQuanYi Zen Hei", "Noto Sans CJK SC", sans-serif;
          font-size: 10.5pt; line-height: 1.65; color: #222; max-width: 100%; }}
  h1 {{ font-size: 20pt; border-bottom: 3px solid #2E86DE; padding-bottom: 8px; margin-top: 0; }}
  h2 {{ font-size: 15pt; color: #1a5490; border-left: 5px solid #2E86DE; padding-left: 10px;
        margin-top: 26px; page-break-after: avoid; }}
  h3 {{ font-size: 12.5pt; color: #333; margin-top: 18px; page-break-after: avoid; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 9pt;
           page-break-inside: avoid; }}
  th {{ background: #2E86DE; color: #fff; padding: 6px 8px; text-align: left; font-weight: normal; }}
  td {{ border: 1px solid #d8dee6; padding: 5px 8px; }}
  tr:nth-child(even) td {{ background: #f6f9fd; }}
  blockquote {{ background: #f3f8ff; border-left: 4px solid #2E86DE; margin: 12px 0;
                padding: 8px 14px; color: #33475b; }}
  code {{ background: #f2f4f7; padding: 1px 5px; border-radius: 3px; font-size: 9pt; }}
  pre {{ background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 5px; padding: 10px;
         overflow-x: auto; page-break-inside: avoid; }}
  pre code {{ background: none; }}
  hr {{ border: none; border-top: 1px solid #dbe2ea; margin: 22px 0; }}
  img {{ max-width: 100%; height: auto; display: block; margin: 14px auto;
         page-break-inside: avoid; border: 1px solid #e6ebf1; }}
  strong {{ color: #0b2d52; }}
  ul, ol {{ padding-left: 22px; }}
  a {{ color: #2E86DE; }}
</style></head><body>
{body}
</body></html>"""

    html_path = base + '.html'
    open(html_path, 'w', encoding='utf-8').write(html)

    pdf_path = base + '.pdf'
    subprocess.run([CHROME, '--headless', '--disable-gpu', '--no-sandbox',
                    '--no-pdf-header-footer', f'--print-to-pdf={pdf_path}',
                    '--virtual-time-budget=8000', f'file://{os.path.abspath(html_path)}'],
                   check=True, capture_output=True, timeout=180)
    print(f'✅ {html_path}')
    print(f'✅ {pdf_path}  ({os.path.getsize(pdf_path)//1024} KB)')

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
