import tkinter as tk
from tkinter import scrolledtext
import threading
import webbrowser
import re
from agent import agent_respond

class JiraBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jira Agent")
        self.root.geometry("500x600")
        self.root.configure(bg="#2c3e50")

        self.chat_history = [{"role": "system", "content": "You are a helpful Jira assistant."}]

        # --- UI Components ---
        
        # Header
        header = tk.Label(root, text="Jira Assistant", font=("Arial", 16, "bold"), bg="#2c3e50", fg="white", pady=10)
        header.pack(fill=tk.X)

        # Chat Display Area
        self.chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10), bg="#ecf0f1", fg="#2c3e50")
        self.chat_display.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED) # Read-only initially

        # Input Area Frame
        input_frame = tk.Frame(root, bg="#2c3e50")
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        # Input Box
        self.user_input = tk.Entry(input_frame, font=("Arial", 12))
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", self.send_message)

        # Send Button
        send_btn = tk.Button(input_frame, text="Send", command=self.send_message, bg="#27ae60", fg="white", font=("Arial", 10, "bold"))
        send_btn.pack(side=tk.RIGHT)

        # Status Bar (for loading state)
        self.status_label = tk.Label(root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#34495e", fg="#bdc3c7")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
    def extract_jira_link(self,text):
        pattern=r"https?://[^\s]+/browse/[A-Z]+-\d+"
        match=re.search(pattern,text)
        return match.group(0) if match else None

    def send_message(self, event=None):
        msg = self.user_input.get()
        if not msg:
            return

        # Display User Message
        self.append_chat("You", msg)
        self.user_input.delete(0, tk.END)

        # Start loading state
        self.status_label.config(text="Thinking & accessing Jira...")
        self.root.update()

        # Run logic in a separate thread to keep UI responsive
        threading.Thread(target=self.get_response, args=(msg,)).start()

    def get_response(self, user_msg,):
        try:
            # Call the AI Agent
            
            response = agent_respond(user_msg,self.chat_history)
            self.chat_history.append({"role": "user", "content": user_msg})
            self.chat_history.append({"role": "assistant", "content": response})

            # Update UI (Must be done on main thread)
            self.root.after(0, self.append_chat, "Bot", response)
            self.root.after(0, lambda: self.status_label.config(text="Ready"))
            
        except Exception as e:
            self.root.after(0, self.append_chat, "System", f"Error: {e}")
            self.root.after(0, lambda: self.status_label.config(text="Error occurred"))

    def append_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)

        self.chat_display.tag_config("user", foreground="#2980b9", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("bot", foreground="#c0392b", font=("Arial", 10, "bold"))

        tag = "user" if sender == "You" else "bot"

        self.chat_display.insert(tk.END, f"{sender}: ", tag)
        self.chat_display.insert(tk.END, f"{message}\n")

    # ---- Check for Jira link and add button ----
        if sender == "Bot":
            link = self.extract_jira_link(message)
            if link:
                btn = tk.Button(
                    self.chat_display,
                    text="Open in Jira",
                    bg="#2980b9",
                    fg="white",
                    cursor="hand2",
                    command=lambda url=link: webbrowser.open(url)
            )
                self.chat_display.window_create(tk.END, window=btn)
                self.chat_display.insert(tk.END, "\n")

        self.chat_display.insert(tk.END, "\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = JiraBotApp(root)
    root.mainloop()