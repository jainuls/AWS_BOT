import speech_recognition as sr
import boto3
import pyttsx3
import tkinter as tk
from tkinter import messagebox,ttk, StringVar

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

# Define global variable for AMIs
amis = [
    {'Id': 'ami-00d990e7e5ece7974', 'Description': 'Microsoft Windows Server 2022 Full Locale English AMI provided by Amazon'},
    {'Id': 'ami-0d699cf0fdfe1e86d', 'Description': 'Microsoft Windows Server 2022 Core Locale English AMI provided by Amazon'},
    {'Id': 'ami-035d8ae8de3734e5a', 'Description': 'Microsoft Windows Server 2019 with Desktop Experience Locale English AMI provided by Amazon'},
    {'Id': 'ami-035d8ae8de3734e5a', 'Description': 'Microsoft Windows Server 2019 with Desktop Experience Locale English AMI provided by Amazon'},
    {'Id': 'ami-0aca05dd8c2f99518', 'Description': 'Microsoft Windows Server 2019 Core Locale English AMI provided by Amazon'},
    {'Id': 'ami-0a749d160bf052e89', 'Description': 'Microsoft Windows Server 2016 with Desktop Experience Locale English AMI provided by Amazon'},
    {'Id': 'ami-0e731c8a588258d0d', 'Description': 'Amazon Linux 2023 AMI 2023.3.20240205.2 x86_64 HVM kernel-6.1'},
    {'Id': 'ami-0cf10cdf9fcd62d37', 'Description': 'Amazon Linux 2 Kernel 5.10 AMI 2.0.20240131.0 x86_64 HVM gp2'},
    {'Id': 'ami-0c7217cdde317cfec', 'Description': 'Canonical, Ubuntu, 22.04 LTS, amd64 jammy image build on 2023-12-07'},
    {'Id': 'ami-06aa3f7caf3a30282', 'Description': 'Canonical, Ubuntu, 20.04 LTS, amd64 focal image build on 2023-10-25'},
    {'Id': 'ami-0fe630eb857a6ec83', 'Description': 'Provided by Red Hat, Inc.'},
    {'Id': 'ami-058bd2d568351da34', 'Description': 'Debian 12 (20231013-1532)'}
]

# Define instance types
instance_types = [
    't2.micro', 't2.medium',
    'm4.large', 'm4.xlarge',
    'c4.large', 'c4.xlarge',
    'r4.large', 'r4.xlarge'
]

def create_ec2_instance(ami_id, instance_type, key_name=None, name_tag=None):
    try:
        # Create EC2 instance with or without key pair
        if key_name:
            instance = ec2_resource.create_instances(
                ImageId=ami_id,
                InstanceType=instance_type,
                MaxCount=1,
                MinCount=1,
                KeyName=key_name,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': name_tag} if name_tag else {}
                        ]
                    }
                ]
            )[0]
        else:
            instance = ec2_resource.create_instances(
                ImageId=ami_id,
                InstanceType=instance_type,
                MaxCount=1,
                MinCount=1,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': name_tag} if name_tag else {}
                        ]
                    }
                ]
            )[0]

        # Wait for instance to be running
        instance.wait_until_running()

        # Get the security group ID from the instance
        security_group_id = instance.security_groups[0]['GroupId']

        messagebox.showinfo("EC2 Instance Created", f"EC2 instance created successfully!\nInstance ID: {instance.id}")
        # Insert a record into the access_history table
        cursor.execute("INSERT INTO access_history (service_name, service_id, action_type, action_date) VALUES ('EC2', %s, 'create', %s)", (instance.id, datetime.datetime.now(),))
        db.commit()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create EC2 instance: {e}")
        
def create_key_pair(key_name):
    try:
        response = ec2_client.create_key_pair(KeyName=key_name)
        with open(f"{key_name}.pem", "w") as key_file:
            key_file.write(response['KeyMaterial'])
        messagebox.showinfo("Key Pair Created", f"Key pair '{key_name}' created successfully!\nPrivate key saved to {key_name}.pem")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create key pair: {e}")

def list_key_pairs():
    try:
        response = ec2_client.describe_key_pairs()
        key_pairs = [key_pair['KeyName'] for key_pair in response['KeyPairs']]
        return key_pairs
    except Exception as e:
        messagebox.showerror("Error", f"Failed to list key pairs: {e}")
        return []

ami_tree = None  # Declare ami_tree as a global variable

def display_amis():
    global ami_tree  # Use the global ami_tree variable
    if ami_tree is not None:
        # Clear existing data
        for item in ami_tree.get_children():
            ami_tree.delete(item)
        for i, ami in enumerate(amis, start=1):
            ami_tree.insert('', 'end', values=(i, ami['Id'], ami['Description']))

def handle_voice_command():
    global ami_tree  # Use the global ami_tree variable
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
            engine.say("you said " + "{}".format(value))      
            engine.runAndWait()                  
            if value.lower() == 'create instance' or 'instance':
                if ami_tree is None:
                    ami_tree = ttk.Treeview(frame, columns=('Index', 'Id', 'Description'), show='headings')
                    ami_tree.heading('Index', text='Index')
                    ami_tree.heading('Id', text='AMI Id')
                    ami_tree.heading('Description', text='Description')
                    ami_tree.delete(*ami_tree.get_children())  # Clear existing data
                    ami_tree.column('#0', width=50)  # Set width for index column
                    ami_tree.column('Id', width=200)  # Set width for ID column
                    ami_tree.column('Description', width=300)  # Set width for Description column
                    for i, ami in enumerate(amis, start=1):
                        ami_tree.insert('', 'end', values=(i, ami['Id'], ami['Description']))
                    ami_tree.pack(anchor=tk.W, padx=20, pady=5)
                display_amis()
                ami_index_label.pack(anchor=tk.W, padx=20, pady=5)
                ami_index_entry.pack(anchor=tk.W, padx=20, pady=5)
                instance_type_label.pack(anchor=tk.W, padx=20, pady=5)
                instance_type_frame.pack(anchor=tk.W, padx=20, pady=5)  # Pack the instance type frame
                name_tag_label.pack(anchor=tk.W, padx=20, pady=5)
                name_tag_entry.pack(anchor=tk.W, padx=20, pady=5)
                create_key_choice_label.pack(anchor=tk.W, padx=20, pady=5)
                create_key_choice_entry.pack(anchor=tk.W, padx=20, pady=5)
                start_create_button.pack(anchor=tk.W, padx=20, pady=5)

            else:
                engine.say("Oops! Didn't catch that. Please try again")
                engine.runAndWait()
                
        except sr.UnknownValueError:
            engine.say("Invalid command. Please try again with valid command") 
            engine.runAndWait()     
       
    except KeyboardInterrupt:
        pass

def start_create_instance():
    create_key_choice = create_key_choice_entry.get().lower()
    if create_key_choice == 'yes':
        key_name_label.pack(anchor=tk.W, padx=20, pady=5)
        key_name_entry.pack(anchor=tk.W, padx=20, pady=5)
        create_key_button.pack(anchor=tk.W, padx=20, pady=5)
        start_create_button.pack_forget()
    elif create_key_choice == 'no':
        existing_key_name_label.pack(anchor=tk.W, padx=20, pady=5)
        existing_key_name_entry.pack(anchor=tk.W, padx=20, pady=5)
        create_instance_button.pack(anchor=tk.W, padx=20, pady=5)
        start_create_button.pack_forget()
    else:
         messagebox.showerror("Error","Fill all the required Details to create Instance")

def create_instance():
    selected_ami_index = int(ami_index_entry.get()) - 1
    ami_id = amis[selected_ami_index]['Id']
    instance_type = instance_type_var.get()  # Get the selected instance type
    create_key_choice = create_key_choice_entry.get().lower()
    name_tag = name_tag_entry.get()
    
    if create_key_choice == 'yes':
        key_name = key_name_entry.get()
        create_key_pair(key_name)
        create_ec2_instance(ami_id, instance_type, key_name, name_tag)
    elif create_key_choice == 'no':
        existing_key_name = existing_key_name_entry.get()
        create_ec2_instance(ami_id, instance_type, existing_key_name, name_tag)
    else:
        messagebox.showerror("Error","Invalid choice")

def end_bot():
    root.destroy()
    db.close()  # Close the database connection

# Create tkinter GUI
root = tk.Tk()
root.title("EC2 Instance Creation Management")
root.geometry("1000x700")
root.configure(bg="#1F2937")  # Matte dark blue

style = ttk.Style()
style.theme_use("clam")

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

ami_index_label = ttk.Label(frame, text="AMI Index:", style="Label.TLabel")
ami_index_entry = ttk.Entry(frame, width=30)
instance_type_label = ttk.Label(frame, text="Instance Type:", style="Label.TLabel")
# Create a frame for instance type radio buttons
instance_type_frame = ttk.Frame(frame)
instance_type_var = StringVar()
for instance_type in instance_types:
    radio_button = ttk.Radiobutton(instance_type_frame, text=instance_type, variable=instance_type_var, value=instance_type, style="TRadiobutton")
    radio_button.pack(anchor=tk.W)

name_tag_label = ttk.Label(frame, text="Instance Tag 'Name':", style="Label.TLabel")
name_tag_entry = ttk.Entry(frame, width=30)
create_key_choice_label = ttk.Label(frame, text="Create Key Pair? (yes/no):", style="Label.TLabel")
create_key_choice_entry = ttk.Entry(frame, width=30)

start_create_button = ttk.Button(frame, text="Start Creating Instance", command=start_create_instance, style="Accent.TButton")

key_name_label = ttk.Label(frame, text="Enter New Key Name:", style="Label.TLabel")
key_name_entry = ttk.Entry(frame, width=30)
existing_key_name_label = ttk.Label(frame, text="Enter Existing Key Name:", style="Label.TLabel")
existing_key_name_entry = ttk.Entry(frame, width=30)
create_instance_button = ttk.Button(frame, text="Create Instance", command=create_instance, style="Accent.TButton")
create_key_button = ttk.Button(frame, text="Create Instance", command=create_instance, style="Accent.TButton")

def update_key_name_entry():
    if create_key_choice_entry.get().lower() == 'yes':
        key_name_label.pack(anchor=tk.W, padx=20, pady=5)
        key_name_entry.pack(anchor=tk.W, padx=20, pady=5)
        create_key_button.pack(anchor=tk.W, padx=20, pady=5)
        start_create_button.pack_forget()  # Hide the "Start Creating Instance" button
    else:
        existing_key_name_label.pack(anchor=tk.W, padx=20, pady=5)
        existing_key_name_entry.pack(anchor=tk.W, padx=20, pady=5)
        create_instance_button.pack(anchor=tk.W, padx=20, pady=5)
        start_create_button.pack_forget()  # Hide the "Start Creating Instance" button
        existing_key_pairs = list_key_pairs()
        if existing_key_pairs:
            messagebox.showinfo("Existing Key Pairs\n", f"Existing key pairs:\n\n{'\n '.join(existing_key_pairs)}")

create_key_choice_entry.bind('<FocusOut>', lambda e: update_key_name_entry())

root.mainloop()