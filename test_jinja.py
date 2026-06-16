from flask import Flask, render_template_string

app = Flask(__name__)
with app.app_context():
    try:
        print(render_template_string('{{ ev.tipo|upper }}', ev={'tipo': None}))
    except Exception as e:
        print("EXCEPTION:", e)
