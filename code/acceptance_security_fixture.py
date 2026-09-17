"""Acceptance-only static scan fixture. Never execute, merge or deploy."""
from flask import Flask, request

app = Flask(__name__)

@app.get("/acceptance-only")
def unsafe_expression():
    return str(eval(request.args["expression"]))
