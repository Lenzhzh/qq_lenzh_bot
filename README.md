# qq-latexmd-bot

~~这是一个用于渲染qq中markdown语法和LaTex语法的机器人。至少过去是的~~

而现在这是一个集成了各种功能的机器人。

## 项目原理

通过NapCatQQ等监听QQ消息并用websockets传递到NoneBot项目中。通过创建无头浏览器并截图的方式将md/latex转换为图像。

## 快速开始

1. 环境搭建

    在windows 11下，请确保你的电脑中安装了 python3 且版本合适（开发中使用的是 python 3.13.0），cmd运行如下命令：

    ```bash
    git clone git@github.com:Lenzhzh/qq-latexmd-bot.git
    cd ./qq-latexmd-bot
    python -m venv .venv
    ./.venv/Script/activate
    pip install requirements.txt -r
    playwright install
    ```

    该命令会创建虚拟环境并安装所需的依赖库。如果这个过程太慢，可以考虑换国内源。

2. 配置NapCatQQ

    前往 [NapCatQQ官网](https://napneko.github.io/guide/napcat) 进行下载NapCatQQ的release版本。推荐使用 [可视化版本](https://github.com/NapNeko/NapCatQQ-Desktop) 方便上手。

    本工具开发过程中使用的就是可视化版本，推荐初学者跟随使用。

    初步配置过程可以参考官方文档，这里给出进一步的配置过程。

    ![alt text](/img/image.png)

    选择连接设置，选择新增连接设置 -> websockets客户端，会弹出以下窗口

    ![alt text](/img/image-1.png)

    在URL栏中填入 `ws://localhost:8080/onebot/v11/ws`。其中ip和端口可以根据你的服务器地址或是端口修改。

    选择 启用 -> OK -> 更新配置 -> 启动

    如果你发现 `NapCatQQ` 已经登上了你的bot，那么恭喜你成功了喵~

3. 启动机器人

    启动机器人前，你会发现目录里有一个叫做 `.env` 的文件。务必保证上面的 `host` 和 `port` 与你在 `NatCapQQ` 中设置的保持一致。

    机器人基于onebot v11，且基于noneBot搭建。因此你需要在cmd中运行:

    ```bash
    nb run
    ```
    如果提示你nb不是一个可执行文件，这可能是由于某些奇怪的原因，建议上网查询。大部分情况下会需要你修改环境变量。

    此后会提示机器人已经展开侦听，在 `NapCat` 上点击重启或启用就行了~

4. 更多的功能

    如果需要使用latex支持，需要从github上下载(mathjax源码)[https://github.com/mathjax/MathJax/releases/], 下载源码解压后放入 `qq_latexmd_bot\plugins\mdlatex_render` 文件夹，并将文件夹命名为 `MathJax`。

    如果想要使用mermaid同理。请下载源码。由于mermaid只有一个单文件，你不需要使用相应的文件夹，直接命名为 mermaid.js 即可。
    
    开发中使用的是cdn的mermaid，直接复制 [国内源cdn](https://cdn.bootcdn.net/ajax/libs/mermaid/9.4.3/mermaid.min.js) 网站中的文字内容即可。

## How to start

1. generate project using `nb create` .
2. create your plugin using `nb plugin create` .
3. writing your plugins under `qq_latexmd_bot/plugins` folder.
4. run your bot using `nb run --reload` .

## Documentation

See [Docs](https://nonebot.dev/)
