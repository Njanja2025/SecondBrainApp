import os

TASK_FILE = "src/ai_agent/agent_tasks.txt"

def send_command(cmd):
    with open(TASK_FILE, "a") as f:
        f.write(cmd + "\n")
    print(f"Sent command to Baddy: {cmd}")

def main():
    print("Baddy Interface Active. Type a command:")
    while True:
        user_input = input(">>> ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break
        send_command(user_input)

if __name__ == "__main__":
    main() 