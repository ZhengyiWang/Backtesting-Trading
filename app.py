import gradio as gr
import requests
import json
import datetime
from quantitative import BackTraderUtils

# 通义千问的API
TYQW_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"




# 这是一个模拟的后台线程，用于从 SSE 接收数据
def fetch_backtrade_data(
        stock_code: str,
        hq_begin_date: datetime,
        hq_end_date: datetime,
        strategy: str
):
    if not stock_code:
        raise ValueError("请输入股票代码！")
    if not hq_begin_date:
        raise ValueError("请选择行情开始日期！")
    if not hq_end_date:
        raise ValueError("请选择行情结束日期！")
    if not strategy:
        raise ValueError("请选择策略！")

    # 回测结果
    backtrade_ret = BackTraderUtils.back_test(ticker_symbol=stock_code, start_date=hq_begin_date, end_date=hq_end_date, strategy=strategy)

    # 系统提示词
    sys_prompt = '你是一个乐于助人的助手，你不说废话和套话，你说话通俗易懂，你分析内容深刻有思考。'

    # 用户提示词
    usr_prompt = f'''
        ```xml
        <task_description>
        撰写一篇策略回测分析报告，详细解析下述backtrade回测策略返回的内容，包括但不限于策略回测情况的整体总结、回报总结、风险总结、交易过程分析等。内容为空或者none的字段不做分析，金额单位是元。以markdown格式输出。
        </task_description>
        
        回测策略名称：{strategy}
        策略回测结果：{backtrade_ret}
        
        <instructions>
        1. 根据回测策略名称，简单一小段话介绍回测的策略原理，以及优势和风险，要求语言简洁，通俗易懂。
        2. 总结策略回测地整体情况，包括但不限于Starting Portfolio Value和Final Portfolio Value的陈述与对比分析，回报率（rtot）、平均回报率（ravg）、标准化回报率（rnorm）、夏普比率Sharpe Ratio等的分析。
        3. 分析策略回测的风险情况，包括但不限于最大回撤（Drawdown）、最大回撤期间损失的资金（moneydown）等。
        4. 对交易过程进行数据上的概括总结，并对交易过程内容进行归纳分析，点出收益最亮眼的交易操作。
        </instructions>
        ```
    '''

    # 发送请求
    headers = {'Accept': 'text/event-stream', 'Content-Type': 'application/json', 'Authorization': 'Bearer sk-2a72a0e44e8147099b2e6d30118da2ad'}
    data = {
        "messages": [
            {
                "role": "system",
                "content": sys_prompt
            },
            {
                "role": "user",
                "content": usr_prompt
            }
        ],
        "model": "qwen-long",
        "stream": True,
        "temperature": 0
    }
    resp = requests.post(TYQW_URL, data=json.dumps(data), stream=True, headers=headers)
    # 确保请求成功
    resp.raise_for_status()
    out_str = ''
    for line in resp.iter_lines():
        if line and not('[DONE]' in line.decode('utf-8').strip()):
            # print(line)
            decoded_line = line.decode('utf-8').strip()
            json_str = decoded_line[5:]
            # print(json_str)
            json_obj = json.loads(json_str)
            chunk = json_obj['choices'][0]['delta']['content']
            print(chunk)
            out_str = out_str + chunk
            yield out_str
# 样式
css = """
body {
    overflow: hidden;
}

gradio-app {
    width: 100vw !important;
    height: 100vh !important;
    padding: 3px;
    position: absolute;
    background: #ffe !important;
}

div.prose {
    height: 600px;
    overflow-y: scroll;
    border: 1px solid #ccc;
    padding: 10px;
    background-color: white;
    border-radius: 10px;
}

div.prose::-webkit-scrollbar {
    display: block;
    width: 0;
    height: auto;
}

div.prose::-webkit-scrollbar-track {  
    background: #f1f1f1;
    border-radius: 2px;
}  

div.prose::-webkit-scrollbar-thumb {  
    background: #888;
    border-radius: 2px;
}

div.prose::-webkit-scrollbar-thumb:hover {  
    background: #555;  
}

.float {
    display: none;
}

.block.svelte-12cmxck:not(.padded) {
    background-color: transparent;
    border: 0 !important;
    box-shadow: none;
}
"""

js = """
function () {
    let screenWidth = screen.availWidth; // 获取屏幕宽度
    let screenHeight = screen.availHeight; // 获取屏幕高度
    let speed = 100; // 雪花下落的速度

    function Snow(size, downSize) {
        this.box = document.querySelector('gradio-app'); // 获取容器元素
        this.size = size; // 雪花数量
        this.downSize = downSize || 10; // 每次落下的雪花数量，默认为10个
        this.item = []; // 雪花元素数组
        this.init(); // 初始化
        this.start(); // 开始下雪
    }

    // 获取相关随机数据的方法
    Snow.prototype.getRandomThings = function (type) {
        let res;
        if (type == 'left') { // 初始的left
            res = Math.round(Math.random() * (screenWidth - 30 - 10)) + 10; // 随机生成left值
            Math.random() > 0.8 ? (res = -res) : null; // 80%的概率使左边的雪花出现在左侧（left为负值）
        } else if (type == 'top') { // 初始的top
            res = -(Math.round(Math.random() * (50 - 40)) + 40); // 随机生成top值，负值使雪花在屏幕上方
        } else if (type == 'incre') { // 向下的速度
            res = Math.random() * (4 - 1) + 1; // 随机生成向下的速度
        } else if (type == 'increLeft') { // 向右的速度
            res = Math.random() * (0.8 - 0.5) + 0.5; // 随机生成向右的速度
        } else { // 雪花的大小
            res = Math.round(Math.random() * (30 - 10)) + 10; // 随机生成雪花的大小
        }
        return res;
    }

    Snow.prototype.init = function () {
        this.box.style.width = screenWidth + 'px'; // 设置容器宽度为屏幕宽度
        this.box.style.height = screenHeight + 'px'; // 设置容器高度为屏幕高度
        let fragment = document.createDocumentFragment(); // 创建文档片段，用于性能优化
        for (let i = 0; i < this.size; i++) { // 创建雪花元素
            let left = this.getRandomThings('left'); // 获取随机的left值
            let top = this.getRandomThings('top'); // 获取随机的top值
            let snowSize = this.getRandomThings('size'); // 获取随机的雪花大小
            let snow = document.createElement("div"); // 创建雪花元素
            snow.style.cssText = 'position:absolute;color:#FFFFFF;'; // 设置元素样式
            snow.style['font-size'] = snowSize + 'px'; // 设置字体大小
            snow.style.left = left + 'px'; // 设置left值
            snow.style.top = top + 'px'; // 设置top值
            //snow.innerHTML = '&#10052'; // 设置雪花图标（Unicode编码）
            snow.innerHTML = '💸'; // 设置雪花图标（Unicode编码）
            this.item.push(snow); // 添加到雪花元素数组中
            fragment.appendChild(snow); // 添加到文档片段中
        }
        this.box.appendChild(fragment); // 将文档片段添加到容器中
    }

    Snow.prototype.start = function () {
        let that = this;
        let num = 0;
        for (let i = 0; i < this.size; i++) { // 遍历雪花元素数组
            let snow = this.item[i];
            if ((i + 1) % this.downSize == 0) { // 每downSize个雪花一组，控制下落速度
                num++;
            }
            (function (s, n) { // 使用闭包保存snow和num的值
                setTimeout(function () { // 定时器，实现雪花分批下落
                    that.doStart(s); // 调用doStart方法使雪花开始下落
                }, 1000 * n) // 每隔n秒下落一组雪花
            })(snow, num)
        }
    }

    // 针对每个雪花的定时处理
    Snow.prototype.doStart = function (snow) {
        let that = this;
        (function (s) {
            let increTop = that.getRandomThings('incre'); // 获取向下的速度
            let increLeft = that.getRandomThings('increLeft'); // 获取向右的速度
            let x = parseInt(getStyle(s, 'left')), y = parseInt(getStyle(s, 'top')); // 获取当前的left和top值

            if (s.timmer) return; // 如果定时器已存在，则不执行后续代码
            s.timmer = setInterval(function () { // 设置定时器，使雪花动起来
                // 超过右边或者底部重新开始
                if (y > (screenHeight - 5) || x > (screenWidth - 30)) {
                    // 重新回到天上开始往下
                    increTop = that.getRandomThings('incre');
                    increLeft = that.getRandomThings('increLeft');

                    // 重新随机属性
                    let left = that.getRandomThings('left');
                    let top = that.getRandomThings('top');
                    let snowSize = that.getRandomThings('size');
                    s.style.left = left + 'px';
                    s.style.top = top + 'px';
                    s.style['font-size'] = snowSize + 'px';
                    y = top;
                    x = left;
                    n = 0;

                    return;
                }

                // 加上系数，当随机数大于0.5时速度加快，小于0.5时速度减慢，形成飘动效果
                x += Math.random() > 0.5 ? increLeft * 1.1 : increLeft * 0.9;
                y += Math.random() > 0.5 ? increTop * 1.1 : increTop * 0.9;

                // 设置left和top值使雪花动起来
                s.style.left = x + 'px';
                s.style.top = y + 'px';
            }, speed); // 每隔speed毫秒执行一次定时器中的代码
        })(snow)
    }

    // 获取元素的样式值
    function getStyle(obj, prop) {
        let prevComputedStyle = document.defaultView ? document.defaultView.getComputedStyle(obj, null) : obj.currentStyle;
        return prevComputedStyle[prop];
    }

    new Snow(30, 1); // 创建一个Snow对象，传入雪花数量和每批下落的雪花数量
}
"""

with gr.Blocks(css=css, js=js, title='量化策略之狼') as demo:
    title = gr.Label(value='量化回测神器', color=None)
    #输入表单横向布局
    with gr.Row():
        # 设置输出组件
        md = gr.Markdown()
        with gr.Column():
            # 输入股票代码
            stock_input = gr.Textbox(label="输入股票代码，如：600095.SH")
            # 选择行情开始日期
            hq_begin_date_sel = gr.Textbox(label='行情开始日期，如：20200101')
            # 选择行情结束日期
            hq_end_date_sel = gr.Textbox(label='行情结束日期，如：20201231')
            # 选择策略
            strategy_sel = gr.Dropdown(type='value', label='策略', choices=['TurtleStrategy:TurtleStrategy', 'harami:haramiStrategy', 'average_profit_macd:MACDStrategy', 'kdj:KDJStrategy', 'kdj_macd:KdjMacdStrategy', 'SmaStrategy:SmaStrategy'])
            # 设置按钮
            btn = gr.Button("开始回测")
    # 设置按钮点击事件
    btn.click(fn=fetch_backtrade_data, inputs=[stock_input, hq_begin_date_sel, hq_end_date_sel, strategy_sel], outputs=md)

demo.queue()
demo.launch(server_name='0.0.0.0')
