# tools/resend_mail_tool.py
import requests
import os

class ResendMailTool:
    name = "send_via_resend"
    description = "通过 Resend API 发送邮件。作为 Gmail 失败时的备用通道。"
    
    parameters = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "收件人邮箱地址"},
            "subject": {"type": "string", "description": "邮件主题"},
            "body": {"type": "string", "description": "邮件正文内容（支持 HTML）"}
        },
        "required": ["to", "subject", "body"]
    }

    def execute(self, to, subject, body):
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            return "错误：未配置 RESEND_API_KEY 环境变量。"
            
        try:
            # 这是一个标准的 HTTP 请求，VPN 兼容性 100%
            response = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "from": "onboarding@resend.dev", # 初始测试用这个，后面可以绑定域名
                    "to": to,
                    "subject": subject,
                    "html": body
                }
            )
            result = response.json()
            if response.status_code == 200 or response.status_code == 201:
                return f"成功：邮件已通过 Resend 发送至 {to}。ID: {result.get('id')}"
            else:
                return f"Resend API 报错: {result}"
        except Exception as e:
            return f"API 发送过程发生异常: {str(e)}"

resend_tool = ResendMailTool()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": resend_tool.name,
            "description": resend_tool.description,
            "parameters": resend_tool.parameters,
        }
    }
]

TOOL_HANDLERS = {
    resend_tool.name: resend_tool.execute
}