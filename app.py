from flask import Flask, request, Response
from main import handle
import html
import os

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body")

    print("📩 INCOMING:", incoming_msg, flush=True)

    reply = handle(incoming_msg)

    if not reply:
        reply = "לא הבנתי 🤔"

    print("📤 REPLY:", reply, flush=True)

    safe_reply = html.escape(reply)

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{safe_reply}</Message>
</Response>"""

    return Response(twiml, content_type="text/xml; charset=utf-8")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)