from flask import Flask, request
from main import handle

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body")

    # 👉 הבוט שלך
    reply = handle(incoming_msg)

    return f"""
    <Response>
        <Message>{reply}</Message>
    </Response>
    """

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)