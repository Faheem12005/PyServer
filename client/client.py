
import socket
from tqdm import tqdm
import os
import time

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MSG = "!DISCONNECT"
UPLOAD_MSG = "!UPLOAD"
LIST_MSG = "!LIST"
DOWNLOAD_MSG = "!DOWNLOAD"
DELETE_MSG = "!DELETE"
SERVER = "172.20.10.4"
ADDR = (SERVER,PORT)


client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect(ADDR)

        

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' *  (HEADER-len(send_length))
    client.send(send_length)
    client.send(message)


import time

def upload_file():
    send(UPLOAD_MSG)
    cwd = os.getcwd()
    filed = os.path.join(cwd, "files")
    dirlist = os.listdir(filed)

    print("Enter name of the file to upload:")
    file_name = input()
    if file_name in dirlist:
        print(f"{file_name} found!")
        client.send("File found".encode(FORMAT))
        print()
        
        try:
            file_path = os.path.join(filed, file_name)
            with open(file_path, "rb") as file:
                # Send file size
                file_size = os.stat(file_path).st_size
                client.send(str(file_size).encode(FORMAT).ljust(128))
                time.sleep(0.1)  # Small delay to allow server to process
                print("File uploading..")
                # Send file name
                client.send(file_name.encode(FORMAT).ljust(128))
                time.sleep(0.1)  # Small delay to allow server to process

                # Send file content in chunks
                while True:
                    data = file.read(1024)
                    if not data:
                        break
                    client.send(data)

        finally:
            print("File uploaded successfully")
            print()
    else:
        print(f"{file_name} not found!")
        client.send("File not found".encode(FORMAT))
        print()


connected = True
while connected:
    print("-Enter option-\n1.Uploading\n2.Downloading\n3.Listing\n4.Delete\n5.Exit")
    option = int(input())

    if option == 1:
        upload_file()

    elif option == 2:
        send(DOWNLOAD_MSG)
        print("Enter file name to download: ")
        file_name = input()
        send(file_name)
        response = client.recv(128).decode(FORMAT)
        if "file is being deleted" in response:
            print(f"Server Response: {response}")  # Server indicates the file cannot be downloaded
        elif "not found" in response:
            print(f"Server Response: {response}") 
        else:
            file_size = int(response)
            bar = tqdm(range(file_size),f"Recieving {file_name}",unit="B",unit_scale=True,unit_divisor=1024,dynamic_ncols=True,ncols=20)
            with open (f"files/{file_name}","wb") as f:
                bytes_recv = 0
                while bytes_recv<file_size:
                    data = client.recv(1024)
                    if not data:
                        break
                    f.write(data)
                    bytes_recv += len(data)
                    bar.update(len(data))
                    bar.refresh()
            bar.close()

            print("File downloaded succesfully")
            print()

    elif option == 3:
        send(LIST_MSG)
        data = client.recv(1024)
        data = data.decode(FORMAT)
        data = eval(data)
        for i in data:
            print(i)
        print()
    elif option == 4:
        send(DELETE_MSG)
        print("Enter File to be deleted: ")
        file_name = input()
        send(file_name)
        msg = client.recv(1024).decode(FORMAT)
        print(f"Server Response: {msg}")
        print()
    elif option == 5:
        send(DISCONNECT_MSG)
        connected = False
    else:
        print("Enter correct option!")
