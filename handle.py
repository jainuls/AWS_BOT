import speech_recognition as sr
import pyttsx3
import subprocess
import tkinter as tk
from tkinter import ttk
import mysql.connector

# MySQL database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="aws_access_history"
)
cursor = db.cursor()

# Create table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS access_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        service_name VARCHAR(255),
        service_id VARCHAR(255),       
        action_type VARCHAR(255),
        action_date DATETIME
    )
""")

engine = pyttsx3.init()
recognizer = sr.Recognizer()
microphone = sr.Microphone()

access_history_window = None
access_history_tree = None

def handle_voice_command():
    global ami_tree
    try:
        engine.say("Hello Jainul")
        engine.runAndWait()
        engine.say("What can I do for you?")
        engine.runAndWait()
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
        engine.say("Got it!")
        engine.runAndWait()
        try:
            value = recognizer.recognize_google(audio)
            engine.say("You said " + "{}".format(value))
            engine.runAndWait()
            if value.lower() == 'instance creation management' or value.lower() == 'instance creation':
                subprocess.run(["python", "ec2_create.py"])
            elif value.lower() == 'rds' or value.lower() == 'database management' or value.lower() == 'rds management':
                subprocess.run(["python", "rds.py"])
            elif value.lower() == 'instance destroy management' or value.lower() == 'instance destroy':
                subprocess.run(["python", "ec2_destroy.py"])
            elif value.lower() == 'storage management' or value.lower() == 's3':
                subprocess.run(["python", "s3.py"])
            else:
                engine.say("Oops! Didn't catch that. Please try again")
                engine.runAndWait()

        except sr.UnknownValueError:
            engine.say("Oops! Invalid command. Please try again with valid command")
            engine.runAndWait()

    except KeyboardInterrupt:
        pass

def show_access_history():
    global access_history_window, access_history_tree

    if access_history_window is None or not access_history_window.winfo_exists():
        access_history_window = tk.Toplevel(root)
        access_history_window.title("Access History")
        access_history_window.geometry("1000x700")
        access_history_window.configure(bg="#1F2937")  # Matte dark blue

        style = ttk.Style()
        style.theme_use("clam")

        access_history_tree = ttk.Treeview(access_history_window, columns=("Service Name", "Service ID", "Action Type", "Action Date"), show="headings", style="Treeview")
        access_history_tree.heading("Service Name", text="Service Name")
        access_history_tree.heading("Service ID", text="Service ID")
        access_history_tree.heading("Action Type", text="Action Type")
        access_history_tree.heading("Action Date", text="Action Date")
        access_history_tree.pack(fill="both", expand=True, padx=20, pady=20)

        refresh_access_history_button = ttk.Button(access_history_window, text="Refresh", command=refresh_access_history, style="Accent.TButton")
        refresh_access_history_button.pack(pady=10)

        refresh_access_history()
    else:
        access_history_window.deiconify()  # Show the existing window

def refresh_access_history():
    global access_history_tree

    if access_history_tree is not None:
        # Clear the existing data in the treeview
        access_history_tree.delete(*access_history_tree.get_children())

        # Fetch the latest data from the database
        cursor.execute("SELECT service_name, service_id, action_type, action_date FROM access_history")
        rows = cursor.fetchall()

        # Insert the new data into the treeview
        for row in rows:
            access_history_tree.insert("", "end", values=row)
        db.commit()  # Commit the changes to the database

def end_bot():
    root.destroy()
    db.close()  # Close the database connection

root = tk.Tk()
root.title("AWS BOT")
root.geometry("1000x700")
root.configure(bg="#1F2937")  # Matte dark blue

style = ttk.Style()
style.theme_use("clam")

main_frame = ttk.Frame(root, style="Main.TFrame")
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

label = ttk.Label(main_frame, text="Click the button to start voice command", font=("Arial", 16), foreground="#F9FAFB", background="#1F2937")  # White text on matte dark blue
label.pack(pady=20)

start_voice_button = ttk.Button(main_frame, text="Start Voice Command", command=handle_voice_command, style="Accent.TButton")
start_voice_button.pack(pady=10)

end_bot_button = ttk.Button(main_frame, text="End Bot", command=end_bot, style="Accent.TButton")
end_bot_button.pack(pady=10)

menubar = tk.Menu(root, bg="#1F2937", fg="#F9FAFB", activebackground="#4B5563", activeforeground="#F9FAFB")  # Matte colors
root.config(menu=menubar)

access_history_menu = tk.Menu(menubar, bg="#1F2937", fg="#F9FAFB", activebackground="#4B5563", activeforeground="#F9FAFB")  # Matte colors
menubar.add_cascade(label='☰', menu=access_history_menu)
access_history_menu.add_command(label='Access History', command=show_access_history)

root.mainloop()