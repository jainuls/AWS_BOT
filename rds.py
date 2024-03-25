import speech_recognition as sr
import boto3
import pyttsx3
import tkinter as tk
from tkinter import messagebox, Entry, Label, Button, ttk
import mysql.connector
import datetime

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="aws_access_history"
)
cursor = db.cursor()

engine = pyttsx3.init()

# AWS credentials and region
aws_access_key_id = ''
aws_secret_access_key = ''
region_name = 'us-east-1'
rds_client = boto3.client('rds', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)

# Initialize speech recognizer
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Define global variables for widgets used in show_rds_parameters
allocated_storage_label = None
allocated_storage_entry = None
db_name_label = None
db_name_entry = None
engine_label = None
engine_radios = {}
instance_class_label = None
instance_class_radios = {}
username_label = None
username_entry = None
password_label = None
password_entry = None
create_instance_button = None

def create_rds_instance():
    try:
        allocated_storage = int(allocated_storage_entry.get())
        db_instance_identifier = db_name_entry.get()
        engine_key = engine_selection.get()
        db_instance_class = instance_class_options[instance_class_selection.get()]
        master_username = username_entry.get()
        master_password = password_entry.get()

        if not allocated_storage or not db_instance_identifier or not engine_key or not db_instance_class or not master_username or not master_password:
            messagebox.showerror("Error", "All fields are required")
            return

        if len(master_password) < 8 or not any(char.isdigit() for char in master_password) or not any(char.isalpha() for char in master_password):
            messagebox.showerror("Error", "Password must be at least 8 characters long and contain at least one letter and one number")
            return

        response = rds_client.create_db_instance(
            AllocatedStorage=allocated_storage,
            DBInstanceIdentifier=db_instance_identifier,
            Engine=engine_options[engine_key],
            DBInstanceClass=db_instance_class,
            MasterUsername=master_username,
            MasterUserPassword=master_password
        )
        messagebox.showinfo("RDS Instance Created", f"RDS instance '{db_instance_identifier}' created successfully")
        # Insert a record into the access_history table
        cursor.execute("INSERT INTO access_history (service_name, service_id, action_type, action_date) VALUES ('RDS', 'Null', 'create', %s)", (datetime.datetime.now(),))
        db.commit()
    except ValueError:
        messagebox.showerror("Error", "Allocated storage must be a number")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create RDS instance: {e}")

def handle_voice_command():
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

            if value.lower() in ['create rds instance', 'create database', 'database', 'create rds']:
                show_rds_parameters()
            else:
                engine.say("Oops! Didn't catch that. Please try again")
                engine.runAndWait()

        except sr.UnknownValueError:
            engine.say("Oops! Invalid command. Please try again with valid command")
            engine.runAndWait()

    except KeyboardInterrupt:
        pass

def show_rds_parameters():
    global allocated_storage_label, allocated_storage_entry, db_name_label, db_name_entry, engine_label, engine_radios
    global instance_class_label, instance_class_radios, username_label, username_entry, password_label, password_entry, create_instance_button

    allocated_storage_label.pack(anchor=tk.W, padx=20, pady=5)
    allocated_storage_entry.pack(anchor=tk.W, padx=20, pady=5)
    db_name_label.pack(anchor=tk.W, padx=20, pady=5)
    db_name_entry.pack(anchor=tk.W, padx=20, pady=5)
    engine_label.pack(anchor=tk.W, padx=20, pady=5)
    for i, (key, value) in enumerate(engine_options.items(), start=1):
        engine_radios[value].pack(anchor=tk.W, padx=20, pady=5)
    instance_class_label.pack(anchor=tk.W, padx=20, pady=5)
    for i, (key, value) in enumerate(instance_class_options.items(), start=1):
        instance_class_radios[value].pack(anchor=tk.W, padx=20, pady=5)
    username_label.pack(anchor=tk.W, padx=20, pady=5)
    username_entry.pack(anchor=tk.W, padx=20, pady=5)
    password_label.pack(anchor=tk.W, padx=20, pady=5)
    password_entry.pack(anchor=tk.W, padx=20, pady=5)
    create_instance_button.pack(anchor=tk.W, padx=20, pady=5)

def end_bot():
    root.destroy()

# Create tkinter GUI
root = tk.Tk()
root.title("RDS Management")
root.geometry("1000x700")
root.configure(bg="#1F2937")  # Matte dark blue

style = ttk.Style()
style.theme_use("clam")

# Create a custom style for bold labels
style.configure("Bold.TLabel", font=("Arial", 12, "bold"))

main_frame = ttk.Frame(root, style="Main.TFrame")
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

button_frame = ttk.Frame(main_frame, style="Main.TFrame")
button_frame.pack(side="top", pady=20)

label = ttk.Label(button_frame, text="Click the button to start voice command", font=("Arial", 16), foreground="#F9FAFB", background="#1F2937")
label.pack(pady=10)

start_voice_button = ttk.Button(button_frame, text="Start Voice Command", command=handle_voice_command, style="Accent.TButton")
start_voice_button.pack(pady=10)

end_bot_button = ttk.Button(button_frame, text="End Bot", command=end_bot, style="Accent.TButton")
end_bot_button.pack(pady=10)

# Create a canvas to hold the scrollable frame
canvas = tk.Canvas(root)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create a scrollbar for the canvas
scrollbar = tk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Configure the canvas to use the scrollbar
canvas.configure(yscrollcommand=scrollbar.set)

# Create a frame to hold the widgets
frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=frame, anchor='nw')

# Bind the configure event to the frame
def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox('all'))
    canvas_width = event.width
    canvas_height = event.height
    canvas.config(width=canvas_width, height=canvas_height)

frame.bind('<Configure>', on_frame_configure)

# Add RDS-related widgets to the frame
allocated_storage_label = ttk.Label(frame, text="Allocated Storage:", style="Bold.TLabel")
allocated_storage_entry = ttk.Entry(frame, width=30)

db_name_label = ttk.Label(frame, text="DB Name:", style="Bold.TLabel")
db_name_entry = ttk.Entry(frame, width=30)

engine_options = {
    1: "mysql",
    2: "postgres",
    3: "oracle-ee"
}
engine_label = ttk.Label(frame, text="Engine:", style="Bold.TLabel")
engine_selection = tk.IntVar()
engine_radios = {}
for i, (key, value) in enumerate(engine_options.items(), start=1):
    engine_radios[value] = ttk.Radiobutton(frame, text=value, variable=engine_selection, value=key, style="TRadiobutton")

instance_class_options = {
    1: "db.r5.large",
    2: "db.r5.xlarge",
    3: "db.r5.2xlarge"
}
instance_class_label = ttk.Label(frame, text="Instance Class:", style="Bold.TLabel")
instance_class_selection = tk.IntVar()
instance_class_radios = {}
for i, (key, value) in enumerate(instance_class_options.items(), start=1):
    instance_class_radios[value] = ttk.Radiobutton(frame, text=value, variable=instance_class_selection, value=key, style="TRadiobutton")

username_label = ttk.Label(frame, text="Username:", style="Bold.TLabel")
username_entry = ttk.Entry(frame, width=30)

password_label = ttk.Label(frame, text="Password:", style="Bold.TLabel")
password_entry = ttk.Entry(frame, width=30)

create_instance_button = ttk.Button(frame, text="Create RDS Instance", command=create_rds_instance, style="Accent.TButton")

root.mainloop()