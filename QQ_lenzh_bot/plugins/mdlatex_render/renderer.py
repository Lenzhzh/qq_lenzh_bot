import asyncio
import contextlib
from functools import partial
import html
import http.server
import os
import pathlib
import re
import socketserver
import tempfile
from textwrap import dedent
import threading
import time
from playwright.async_api import async_playwright
import markdown as md
from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension
from pygments.formatters import HtmlFormatter
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter

debug = 0
CWD = pathlib.Path(__file__).resolve().parent
STATIC_PATH = CWD / "res"
# MATHJAX_PATH = STATIC_PATH / "MathJax-4.0.0" / "tex-chtml.js"
# MERMAID_PATH = STATIC_PATH / "mermaid.js"

# _html_shell 和 _md_to_html 函数保持不变...
def _html_shell(body_html: str, extra_style: str = "") -> str:
    
    # 使用了cdn的国内源，防止某些情况下无法使用。
    # mathjax_cdn = MATHJAX_PATH.as_uri()
    # mermaid_cdn = MERMAID_PATH.as_uri()

    mathjax_cdn = "/MathJax/tex-chtml.js"
    mermaid_cdn = "/mermaid.js"

    return dedent(f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>render</title>
      <script>
        window.MathJax = {{
          tex: {{ inlineMath: [['$','$'], ['\\\\(','\\\\)']], displayMath: [['$$','$$']] }},
          svg: {{ fontCache: 'global' }}
        }};
      </script>
      <script src="{mathjax_cdn}" defer></script>
      <script src="{mermaid_cdn}"></script>

      <style>
        html, body {{
          margin: 0; padding: 0;
          /* 设置一个透明背景，这样截图时如果需要PNG透明背景会很方便 */
          background: transparent; 
        }}
        .container {{
          box-sizing: border-box;
          max-width: 1000px;
          padding: 24px 28px;
          font: 16px/1.6 -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
                'Noto Sans', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
          color: #1f2328;
          background: #ffffff;
        }}
        .container h1, .container h2, .container h3 {{ margin: 0.8em 0 0.4em; line-height: 1.3; }}
        .container code, .container pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; font-size: 0.95em; }}
        pre code {{ display: block; padding: 12px 14px; border-radius: 6px; overflow-x: auto; background: #f6f8fa; }}
        blockquote {{ margin: 0.8em 0; padding: 0.4em 1em; border-left: 4px solid #d0d7de; color: #57606a; background: #f6f8fa; }}
        img {{ max-width: 100%; }}

        .mermaid {{
          text-align: center;
          padding: 20px 0;
        }}
        {extra_style}
      </style>

      <style>
        {HtmlFormatter(style="default").get_style_defs('.highlight')}
      </style>
    </head>
    <body>
      <div id="root" class="container">{body_html}</div>
	  
	  <script>
        mermaid.initialize({{ 
          startOnLoad: true, 
          theme: 'default' 
        }});
      </script>

	</body>
    </html>
    """).strip()


class SuperCodeBlockPreprocessor(Preprocessor):
	# 这个正则表达式可以捕获语言标识和代码内容
	RE = re.compile(r'```(?P<lang>[\w.-]*)\n(?P<code>.*?)```', re.DOTALL)

	def __init__(self, md):
		super().__init__(md)
		self.formatter = HtmlFormatter(style="default")

	def run(self, lines):
		raw_text = "\n".join(lines)
        
		def replacer(match):
			lang = match.group('lang').strip()
			code = match.group('code').strip()

			if lang == 'mermaid':
				# 代码进行 HTML 编码，确保 > 等符号不会被错误处理
				escaped_code = html.escape(code)

				# 直接构建最终的 HTML 块，Mermaid.js 会正确处理 <pre><code>...</code></pre> 结构
				# 并且由于内容是编码过的，Markdown 解析器不会再动它
				final_html = f'<pre class="mermaid">{escaped_code}</pre>'
				return self.md.htmlStash.store(final_html)
			else:
				# 如果是其他语言，或没有语言标识
				try:
					# 尝试获取对应语言的词法分析器
					lexer = get_lexer_by_name(lang)
				except ValueError:
					# 如果找不到，就当作纯文本处理
					lexer = TextLexer()
				
				# 使用 Pygments 进行语法高亮
				highlighted_code = highlight(code, lexer, self.formatter)
				# Pygments 会生成一个 <div class="highlight"><pre>...</pre></div>
				# 直接存储这个 HTML 块
				return self.md.htmlStash.store(highlighted_code)

		processed_text = self.RE.sub(replacer, raw_text)
		return processed_text.split("\n")

# 加载我们自己的预处理器
class SuperCodeBlockExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(SuperCodeBlockPreprocessor(md), 'super_code_block', 30)

def _md_to_html(md_text: str) -> str:
    # 移除了 'codehilite'，因为它会干扰 Mermaid 的处理
    # 如果你还需要对其他语言（如 python）进行高亮，我们后面可以再把它加回来
    exts = [
        "extra",
        "toc",
        "sane_lists",
        "nl2br",
        SuperCodeBlockExtension(),
    ]
    
    html = md.markdown(md_text, extensions=exts, output_format="html5")
    
    return html

async def _html_to_png_bytes(full_html: str, viewport_width: int = 1100) -> bytes:
	# with tempfile.NamedTemporaryFile(mode='w', suffix='.html', encoding='utf-8', delete=False) as tmp_file:
	# 	tmp_file.write(full_html)
	# 	tmp_file_uri = pathlib.Path(tmp_file.name).as_uri()
		
	# async with async_playwright() as p:
	# 	browser = await p.chromium.launch(headless=not(debug)) # 调试时设为 False
		
	# 	# 1. 设置一个合理的初始视口大小，高度足够即可
	# 	page = await browser.new_page(viewport={"width": viewport_width, "height": 800})
		
	# 	try:
	# 		await page.goto(tmp_file_uri, wait_until="networkidle")

	# 		# 2. 等待 MathJax 和 Mermaid 完全初始化并完成首次渲染 (由于切换本地源已经可以忽略不计)
	# 		# await page.wait_for_function(
	# 		# 	"window.MathJax && window.MathJax.startup && window.MathJax.startup.promise",
	# 		# 	timeout=2000
	# 		# )
	# 		# await page.wait_for_function(
	# 		# 	"window.mermaidPromise",
	# 		# 	timeout=2000
	# 		# )

	# 		# 4. 定位到我们的内容容器
	# 		root_locator = page.locator("#root")

	# 		# 5. 【关键】明确等待元素在屏幕上可见且稳定。
	# 		# 这是防止截图内容为空的核心保证。
	# 		await root_locator.wait_for(state="visible", timeout=3000)
	
	# 		# 通过JS动态修改元素的样式，给它加上外边距
	# 		await root_locator.evaluate("element => element.style.margin = '20px'")
			
	# 		# 7. 对元素进行截图，Playwright 会自动处理滚动和定位
	# 		buf = await root_locator.screenshot(type="png")

	# 		if (debug) : time.sleep(1000)
	# 		return buf

	# 	finally:
	# 		await browser.close()
	# 		os.remove(tmp_file.name)


    # Handler 将根目录设置为 static 文件夹
    # 步骤 1: 设置一个临时的、绑定到特定目录的 Web 服务器
    @contextlib.contextmanager
    def temporary_http_server(directory):
        # 创建一个绑定到指定目录的 Handler 类
        # partial 会创建一个新的函数/类，并预先填入部分参数
        # 这里我们预先填入了 directory 参数给 SimpleHTTPRequestHandler
        Handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
        
        # 0 表示选择一个随机的可用端口
        with socketserver.TCPServer(("127.0.0.1", 0), Handler) as httpd:
            host, port = httpd.server_address
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            try:
                yield f"http://{host}:{port}"
            finally:
                httpd.shutdown()
                server_thread.join()

    # 步骤 2: 在 static 目录中创建临时 HTML 文件
    tmp_html_filename = f"temp_{os.urandom(8).hex()}.html"
    tmp_html_path = STATIC_PATH / tmp_html_filename
    
    with open(tmp_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    # 我们不再需要 os.chdir，这是一个更干净的方案
    original_cwd = os.getcwd() # 保存当前目录，以防万一

    try:
        # 步骤 3: 启动服务器并执行 Playwright 操作
        with temporary_http_server(STATIC_PATH) as server_url:
            page_url = f"{server_url}/{tmp_html_filename}"
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=not(debug))
                page = await browser.new_page(viewport={"width": viewport_width, "height": 800})
                
                try:
                    page.on("console", lambda msg: print(f"Browser Console: {msg.type} >> {msg.text}"))
                    await page.goto(page_url, wait_until="networkidle")

                    root_locator = page.locator("#root")
                    await root_locator.wait_for(state="visible", timeout=15000)
                    await root_locator.evaluate("element => element.style.margin = '20px'")
                    buf = await root_locator.screenshot(type="png")

                    # if debug:
                    #     input("Debug mode: Press Enter to close browser...")
                    
                    return buf
                finally:
                    await browser.close()
    finally:
        # 步骤 4: 清理临时 HTML 文件
        if os.path.exists(tmp_html_path):
            os.remove(tmp_html_path)
        # 确保工作目录恢复原状（虽然我们现在不改它了，但这是好习惯）
        os.chdir(original_cwd)

# —— 对外函数保持不变 —— #
async def render_markdown_image(md_text: str) -> bytes:
    body = _md_to_html(md_text)
    html = _html_shell(body_html=body)
    return await _html_to_png_bytes(html)

async def render_latex_image(tex_text: str) -> bytes:
    stripped = tex_text.strip()
    if not any(mark in stripped for mark in ("$", "\\(", "\\)")):
        stripped = f"$$\n{stripped}\n$$"
    body = f"<div class='latex-wrap'>{stripped}</div>"
    html = _html_shell(
        body_html=body,
        extra_style=".latex-wrap { font-size: 20px; }"
    )
    return await _html_to_png_bytes(html)


# --- 测试代码 ---
async def main():
	test_md = """
# 这是一个标题

这是一个段落，包含一个公式 $E=mc^2$。

$$
\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}
$$

以及一些代码：
```python
def hello():
    print("Hello, World!")
```

以及一些图表:
```mermaid
flowchart LR
	A[开始] --> B[处理]
	B --> C{条件判断}
	C -->|是| D[结果1]
	C -->|否| E[结果2]
```
111
"""
	png_data = await render_markdown_image(test_md)
	with open("test_markdown_output.png", "wb") as f:
		f.write(png_data)
		print("Markdown 图像已保存到 markdown_output.png")

	# png_data_latex = await render_latex_image("\\int_a^b f(x)\\,dx = F(b) - F(a)")
	# with open("latex_output.png", "wb") as f:
	# 	f.write(png_data_latex)
	# print("LaTeX 图像已保存到 latex_output.png")
	
if __name__ == "__main__":
	debug = 1
	asyncio.run(main())