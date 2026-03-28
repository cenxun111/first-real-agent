# tools/gmail_tool.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import socks  # 新增
import socket # 新增
from email.mime.text import MIMEText

class GmailSendTool:
    name = "send_via_gmail"
    description = "通过 Gmail 发送正式邮件。保留用户发件人身份。"
    
    # 【核心】V3.0 安全护栏标记
    requires_approval = True 

    parameters = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "收件人邮箱地址"},
            "subject": {"type": "string", "description": "邮件主题"},
            "body": {"type": "string", "description": "邮件正文内容"}
        },
        "required": ["to", "subject", "body"]
    }



    def execute(self, to, subject, body):
        proxy_host = "127.0.0.1"
        proxy_port = 7891
    
    # 启用远程 DNS (rdns=True)
        socks.set_default_proxy(socks.SOCKS5, proxy_host, proxy_port, rdns=True)
        socket.socket = socks.socksocket 

        try:
            msg = MIMEText(body, 'plain', 'utf-8')
            msg['From'] = os.getenv("GMAIL_USER")
            msg['To'] = to
            msg['Subject'] = subject

            # 【改动点】改回 587 端口
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
            # server.set_debuglevel(1) # 如果还是不行，取消注释这行看详细日志
            
            server.ehlo()      # 向服务器打招呼
            server.starttls()  # 【关键】建立连接后再升级为安全连接，不容易触发 EOF 错误
            server.ehlo()      # 升级后再次打招呼
            
            server.login(os.getenv("GMAIL_USER"), os.getenv("GMAIL_APP_PASSWORD"))
            server.send_message(msg)
            server.quit()
            return f"成功：邮件已发送至 {to}"
        except Exception as e:
            return f"执行失败：{type(e).__name__} - {str(e)}"

gmail_tool = GmailSendTool()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": gmail_tool.name,
            "description": gmail_tool.description,
            "parameters": gmail_tool.parameters,
        }
    }
]

TOOL_HANDLERS = {
    gmail_tool.name: gmail_tool.execute
}