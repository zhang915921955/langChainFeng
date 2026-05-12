import gradio as gr
import os
import time
from chatbot import Chatbot

print("初始化智能客服...")
bot = Chatbot()

def respond(message, chat_history, use_web_search, use_streaming):
    try:
        answer, sources = bot.chat(message, use_web_search=use_web_search)
        response = f"{answer}\n\n**参考来源:**\n" + "\n".join([f"- {src}" for src in sources])
    except Exception as e:
        response = f"抱歉，处理您的问题时发生错误: {str(e)}"
    
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": ""})
    
    if use_streaming:
        for i in range(len(response)):
            chat_history[-1]["content"] = response[:i+1]
            yield "", chat_history.copy()
            time.sleep(0.05)
    else:
        chat_history[-1]["content"] = response
        yield "", chat_history

with gr.Blocks(title="智能客服") as demo:
    gr.Markdown("# 🤖 智能客服系统")
    gr.Markdown("欢迎使用智能客服，我可以回答关于产品、服务和常见问题的咨询。")
    
    chatbot = gr.Chatbot(height=500)
    msg = gr.Textbox(label="输入您的问题")
    
    with gr.Row():
        use_web_search = gr.Checkbox(label="启用联网搜索", value=True)
        use_streaming = gr.Checkbox(label="启用流式响应", value=True)
    
    with gr.Row():
        submit_btn = gr.Button("发送", variant="primary")
        clear_btn = gr.Button("清空对话")
    
    msg.submit(respond, [msg, chatbot, use_web_search, use_streaming], [msg, chatbot])
    submit_btn.click(respond, [msg, chatbot, use_web_search, use_streaming], [msg, chatbot])
    clear_btn.click(lambda: [], None, chatbot, queue=False)

if __name__ == "__main__":
    print("启动 Gradio 应用...")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, favicon_path=None)