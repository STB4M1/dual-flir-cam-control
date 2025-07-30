
# util/log_helper.py

def log_to_textbox(widget, message: str):
    """指定されたテキストボックスにログを出力する"""
    if widget:
        widget.append(message)
