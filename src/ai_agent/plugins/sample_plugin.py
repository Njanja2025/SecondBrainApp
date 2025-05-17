from src.ai_agent.baddy_agent import register_command, log

def handle_sample():
    log("[SamplePlugin] Sample command executed!")

register_command("sample command", handle_sample) 