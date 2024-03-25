import speech_recognition as sr
import boto3
import pyttsx3
import tkinter as tk
from tkinter import messagebox, Entry, Label, Button, ttk, StringVar, Radiobutton, Canvas

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
# Initialize AWS clients
ec2_client = boto3.client('ec2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)
ec2_resource = boto3.resource('ec2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)

# Initialize speech recognizer
recognizer = sr.Recognizer()
microphone = sr.Microphone()

def destroy_ec2_instance(instance_id, instance_name):
    try:
        response = ec2_client.terminate_instances(InstanceIds=[instance_id])
        instance_state = response['TerminatingInstances'][0]['CurrentState']['Name']
        messagebox.showinfo("EC2 Instance Destroyed", f"EC2 instance ID: {instance_id}, Name: {instance_name} is being terminated. Current state: {instance_state}")
        # Insert a record into the access_history table with instance_id
        cursor.execute("INSERT INTO access_history (service_name, service_id, action_type, action_date) VALUES ('EC2', %s, 'destroy', %s)", (instance_id, datetime.datetime.now(),))
        db.commit()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to destroy EC2 instance: {e}")

def handle_voice_command():
    try:
        engine.say("Hello Jainul")
        engine.runAndWait()
        engine.say("What can i do for you?")
        engine.runAndWait()
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
        engine.say("Got it!")
        engine.runAndWait()
        try:
            value = recognizer.recognize_google(audio)
            engine.say("you said " + "{}".format(value))
            engine.runAndWait()
            if value.lower() in ['terminate', 'destroy instance', 'destroy', 'destroyed']:
                display_instances()
                instance_index_label.pack(anchor=tk.W, padx=20, pady=5)
                instance_index_entry.pack(anchor=tk.W, padx=20, pady=5)
                destroy_instance_button.pack(anchor=tk.W, padx=20, pady=5)
            else:
                engine.say("Oops! Didn't catch that. Please try again")
                engine.runAndWait()

        except sr.UnknownValueError:
            engine.say("oops! Invalid command. Please try again with valid command")
            engine.runAndWait()

    except KeyboardInterrupt:
        pass

instance_tree = None
instances = []

def display_instances():
    global instance_tree, instances
    try:
        # Describe instances
        response = ec2_client.describe_instances(Filters=[
            {
                'Name': 'instance-state-name',
                'Values': [
                    'stopped',
                    'running'
                ]
            },
        ])

        # Clear existing data in the treeview
        if instance_tree:
            for item in instance_tree.get_children():
                instance_tree.delete(item)
        else:
            instance_tree = ttk.Treeview(frame, columns=('Index', 'Instance ID', 'Name', 'State'), show='headings')
            instance_tree.heading('Index', text='Index')
            instance_tree.heading('Instance ID', text='Instance ID')
            instance_tree.heading('Name', text='Name')
            instance_tree.heading('State', text='State')
            instance_tree.pack(anchor=tk.W, padx=20, pady=5)

        # Store instances with 'Name' tag
        instances = []
        for i, reservation in enumerate(response['Reservations'], start=1):
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                state = instance['State']['Name']
                name_tag = ''
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        name_tag = tag['Value']
                        break
                instances.append({'Index': i, 'Id': instance_id, 'Name': name_tag, 'State': state})

        # Display instances in the treeview
        for instance in instances:
            instance_tree.insert('', 'end', values=(instance['Index'], instance['Id'], instance['Name'], instance['State']))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to list instances: {e}")

def destroy_instance():
    try:
        instance_index_str = instance_index_entry.get()
        if not instance_index_str.isdigit():
            raise ValueError("Invalid instance index")

        selected_instance_index = int(instance_index_str) - 1
        if 0 <= selected_instance_index < len(instances):
            instance = instances[selected_instance_index]
            instance_id = instance['Id']
            instance_name = instance['Name']
            destroy_ec2_instance(instance_id, instance_name)
        else:
            messagebox.showerror("Error", "Invalid instance index")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to destroy instance: {e}")

def end_bot():
    root.destroy()
    db.close()  # Close the database connection

# Create tkinter GUI
root = tk.Tk()
root.title("EC2 Instance Termination Management")
root.geometry("1000x700")
root.configure(bg="#1F2937")  # Matte dark blue

style = ttk.Style()
style.theme_use("clam")

main_frame = ttk.Frame(root, style="Main.TFrame")
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

label = ttk.Label(main_frame, text="Click the button to start voice command", font=("Arial", 16), foreground="#F9FAFB", background="#1F2937")
label.pack(pady=20)

start_voice_button = ttk.Button(main_frame, text="Start Voice Command", command=handle_voice_command, style="Accent.TButton")
start_voice_button.pack(pady=10)

end_bot_button = ttk.Button(main_frame, text="End Bot", command=end_bot, style="Accent.TButton")
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

instance_index_label = ttk.Label(frame, text="Enter the index of the instance you want to destroy:", style="Label.TLabel")
instance_index_entry = ttk.Entry(frame, width=30)

destroy_instance_button = ttk.Button(frame, text="Destroy Instance", command=destroy_instance, style="Accent.TButton")

root.mainloop()