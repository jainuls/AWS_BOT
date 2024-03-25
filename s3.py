import boto3
import botocore
import tkinter as tk
from tkinter import messagebox, Entry, Label, Button, ttk, StringVar, Radiobutton
import pyttsx3
import speech_recognition as sr
import mysql.connector
import datetime

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="aws_access_history"
)
cursor = db.cursor()
# Initialize AWS credentials and region
aws_access_key_id = ''
aws_secret_access_key = ''
region_name = 'us-east-1'

# Initialize AWS S3 client
s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)

# Initialize speech recognizer
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Initialize text-to-speech engine
engine = pyttsx3.init()

def create_bucket():
    bucket_name = bucket_name_entry.get()
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        messagebox.showinfo("Bucket Created", f"Bucket '{bucket_name}' created successfully!")
        # Insert a record into the access_history table
        cursor.execute("INSERT INTO access_history (service_name, service_id, action_type, action_date) VALUES ('S3_Bucket', %s, 'create', %s)", (bucket_name, datetime.datetime.now(),))
        db.commit()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create bucket: {e}")

def upload_object():
    bucket_name = upload_bucket_name_entry.get()
    local_path = upload_local_path_entry.get()
    s3_key = upload_s3_key_entry.get()
    try:
        s3_client.upload_file(local_path, bucket_name, s3_key)
        messagebox.showinfo("Object Uploaded", f"Object uploaded to '{bucket_name}' with key '{s3_key}'")
        # Insert a record into the access_history table
        cursor.execute("INSERT INTO access_history (service_name, service_id, action_type, action_date) VALUES ('S3_Object', %s, 'upload/create', %s)", (bucket_name, datetime.datetime.now(),))
        db.commit()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to upload object: {e}")

def download_object():
    bucket_name = download_bucket_name_entry.get()
    s3_key = download_s3_key_entry.get()
    local_path = download_local_path_entry.get()
    try:
        s3_client.download_file(bucket_name, s3_key, local_path)
        messagebox.showinfo("Object Downloaded", f"Object downloaded from '{bucket_name}' to '{local_path}'")
        # Insert a record into the access_history table
        cursor.execute("INSERT INTO access_history (service_name, service_id, action_type, action_date) VALUES ('S3_Object', %s, 'download', %s)", (bucket_name, datetime.datetime.now(),))
        db.commit()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download object: {e}")

def delete_object():
    bucket_name = delete_bucket_name_entry.get()
    s3_key = delete_s3_key_entry.get()
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        messagebox.showinfo("Object Deleted", f"Object with key '{s3_key}' deleted from '{bucket_name}'")
        # Insert a record into the access_history table
        cursor.execute("INSERT INTO access_history (service_name, service_id, action_type, action_date) VALUES ('S3_Object', %s, 'delete', %s)", (bucket_name, datetime.datetime.now()))
        db.commit()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete object: {e}")

def delete_bucket():
    bucket_name = delete_bucket_name_entry.get()
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
        messagebox.showinfo("Bucket Deleted", f"Bucket '{bucket_name}' deleted successfully!")
        # Insert a record into the access_history table
        cursor.execute("INSERT INTO access_history (service_name, service_id, action_type, action_date) VALUES ('S3_Bucket', %s, 'delete', %s)", (bucket_name, datetime.datetime.now(),))
        db.commit()
    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketNotEmpty':
            messagebox.showerror("Error", f"Failed to delete bucket: Bucket '{bucket_name}' is not empty. You can force delete it.")
            force_delete_bucket_button.pack(anchor=tk.CENTER, padx=20, pady=5)
            # Insert a record into the access_history table
            cursor.execute("INSERT INTO access_history (service_name, service_id, action_type, action_date) VALUES ('S3_Bucket', %s, 'force_delete', %s)", (bucket_name, datetime.datetime.now(),))
            db.commit()
        else:
            messagebox.showerror("Error", f"Failed to delete bucket: {e}. Check the AWS CLOUDTRAIL logs.")

def force_delete_bucket():
    bucket_name = delete_bucket_name_entry.get()
    try:
        # Delete all objects in the bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={
                    'Objects': [{'Key': obj['Key']} for obj in response['Contents']]
                }
            )
        
        # Delete the bucket
        s3_client.delete_bucket(Bucket=bucket_name)
        messagebox.showinfo("Bucket Deleted", f"Bucket '{bucket_name}' deleted successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to force delete bucket: {e}")


def hide_action_widgets():
    # Hide all action-related widgets
    bucket_name_label.grid_forget()
    bucket_name_entry.grid_forget()
    create_bucket_button.grid_forget()

    upload_bucket_name_label.grid_forget()
    upload_bucket_name_entry.grid_forget()
    upload_local_path_label.grid_forget()
    upload_local_path_entry.grid_forget()
    upload_s3_key_label.grid_forget()
    upload_s3_key_entry.grid_forget()
    upload_object_button.grid_forget()

    download_bucket_name_label.grid_forget()
    download_bucket_name_entry.grid_forget()
    download_s3_key_label.grid_forget()
    download_s3_key_entry.grid_forget()
    download_local_path_label.grid_forget()
    download_local_path_entry.grid_forget()
    download_object_button.grid_forget()

    delete_bucket_name_label.grid_forget()
    delete_bucket_name_entry.grid_forget()
    delete_s3_key_label.grid_forget()
    delete_s3_key_entry.grid_forget()
    delete_object_button.grid_forget()

    delete_bucket_name_label.grid_forget()
    delete_bucket_name_entry.grid_forget()
    delete_bucket_button.grid_forget()
    force_delete_bucket_button.grid_forget()

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

            hide_action_widgets()

            if value.lower() == 'create bucket':
                bucket_name_label.grid(row=0, column=0, padx=10, pady=10)
                bucket_name_entry.grid(row=0, column=1, padx=10, pady=10)
                create_bucket_button.grid(row=0, column=2, padx=10, pady=10)
            elif value.lower() == 'upload object':
                upload_bucket_name_label.grid(row=1, column=0, padx=10, pady=10)
                upload_bucket_name_entry.grid(row=1, column=1, padx=10, pady=10)
                upload_local_path_label.grid(row=2, column=0, padx=10, pady=10)
                upload_local_path_entry.grid(row=2, column=1, padx=10, pady=10)
                upload_s3_key_label.grid(row=3, column=0, padx=10, pady=10)
                upload_s3_key_entry.grid(row=3, column=1, padx=10, pady=10)
                upload_object_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
            elif value.lower() == 'download object':
                download_bucket_name_label.grid(row=5, column=0, padx=10, pady=10)
                download_bucket_name_entry.grid(row=5, column=1, padx=10, pady=10)
                download_s3_key_label.grid(row=6, column=0, padx=10, pady=10)
                download_s3_key_entry.grid(row=6, column=1, padx=10, pady=10)
                download_local_path_label.grid(row=7, column=0, padx=10, pady=10)
                download_local_path_entry.grid(row=7, column=1, padx=10, pady=10)
                download_object_button.grid(row=8, column=0, columnspan=2, padx=10, pady=10)
            elif value.lower() == 'delete object':
                delete_bucket_name_label.grid(row=9, column=0, padx=10, pady=10)
                delete_bucket_name_entry.grid(row=9, column=1, padx=10, pady=10)
                delete_s3_key_label.grid(row=10, column=0, padx=10, pady=10)
                delete_s3_key_entry.grid(row=10, column=1, padx=10, pady=10)
                delete_object_button.grid(row=11, column=0, columnspan=2, padx=10, pady=10)
            elif value.lower() == 'delete bucket':
                delete_bucket_name_label.grid(row=12, column=0, padx=10, pady=10)
                delete_bucket_name_entry.grid(row=12, column=1, padx=10, pady=10)
                delete_bucket_button.grid(row=13, column=0, padx=10, pady=10)
                force_delete_bucket_button.grid(row=13, column=1, padx=10, pady=10)
            else:
                engine.say("Oops! Didn't catch that. Please try again")
                engine.runAndWait()

        except sr.UnknownValueError:
            engine.say("Invalid command. Please try again with a valid command")
            engine.runAndWait()

    except KeyboardInterrupt:
        pass


# Create tkinter GUI
root = tk.Tk()
root.title("S3 Management")
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

end_bot_button = ttk.Button(button_frame, text="End Bot", command=root.destroy, style="Accent.TButton")
end_bot_button.pack(pady=10)

action_frame = ttk.Frame(main_frame, style="Main.TFrame")
action_frame.pack(side="top", fill="both", expand=True, padx=20, pady=20)

# Create widgets for creating bucket
bucket_name_label = ttk.Label(action_frame, text="Bucket Name:", style="Label.TLabel")
bucket_name_entry = ttk.Entry(action_frame, width=30)
create_bucket_button = ttk.Button(action_frame, text="Create Bucket", command=create_bucket, style="Accent.TButton")

# Create widgets for uploading object
upload_bucket_name_label = ttk.Label(action_frame, text="Bucket Name:", style="Label.TLabel")
upload_bucket_name_entry = ttk.Entry(action_frame, width=30)

upload_local_path_label = ttk.Label(action_frame, text="Local File Path:", style="Label.TLabel")
upload_local_path_entry = ttk.Entry(action_frame, width=30)

upload_s3_key_label = ttk.Label(action_frame, text="S3 Key:", style="Label.TLabel")
upload_s3_key_entry = ttk.Entry(action_frame, width=30)

upload_object_button = ttk.Button(action_frame, text="Upload Object", command=upload_object, style="Accent.TButton")

# Create widgets for downloading object
download_bucket_name_label = ttk.Label(action_frame, text="Bucket Name:", style="Label.TLabel")
download_bucket_name_entry = ttk.Entry(action_frame, width=30)

download_s3_key_label = ttk.Label(action_frame, text="S3 Key:", style="Label.TLabel")
download_s3_key_entry = ttk.Entry(action_frame, width=30)

download_local_path_label = ttk.Label(action_frame, text="Local File Path:", style="Label.TLabel")
download_local_path_entry = ttk.Entry(action_frame, width=30)

download_object_button = ttk.Button(action_frame, text="Download Object", command=download_object, style="Accent.TButton")

# Create widgets for deleting object
delete_bucket_name_label = ttk.Label(action_frame, text="Bucket Name:", style="Label.TLabel")
delete_bucket_name_entry = ttk.Entry(action_frame, width=30)

delete_s3_key_label = ttk.Label(action_frame, text="S3 Key:", style="Label.TLabel")
delete_s3_key_entry = ttk.Entry(action_frame, width=30)

delete_object_button= ttk.Button(action_frame, text="Delete Object", command=delete_object, style="Accent.TButton")

# Create widgets for deleting bucket
delete_bucket_name_label = ttk.Label(action_frame, text="Bucket Name:", style="Label.TLabel")
delete_bucket_name_entry = ttk.Entry(action_frame, width=30)

delete_bucket_button = ttk.Button(action_frame, text="Delete Bucket", command=delete_bucket, style="Accent.TButton")
force_delete_bucket_button = ttk.Button(action_frame, text="Force Delete Bucket", command=force_delete_bucket, style="Accent.TButton")

root.mainloop()