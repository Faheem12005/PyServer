import socket
from tqdm import tqdm

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MSG = "!DISCONNECT"
UPLOAD_MSG = "!UPLOAD"
LIST_MSG = "!LIST"
DOWNLOAD_MSG = "!DOWNLOAD"
DELETE_MSG = "!DELETE"
SERVER = "172.20.10.2"
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

connected = True
while connected:
    print("-Enter option-\n1.Uploading\n2.Downloading\n3.Listing\n4.Delete\n5.Exit")
    option = int(input())
    if option == 1:
        send(UPLOAD_MSG)
    if option == 2:
        send(DOWNLOAD_MSG)
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

    if option == 3:
        send(LIST_MSG)
        data = client.recv(1024)
        data = data.decode(FORMAT)
        data = eval(data)
        for i in data:
            print(i)
        print()
    if option == 4:
        send(DELETE_MSG)
        print("Enter File to be deleted: ")
        file_name = input()
        send(file_name)
        msg = client.recv(1024).decode(FORMAT)
        print(f"Server Response: {msg}")
    if option == 5:
        send(DISCONNECT_MSG)
        connected = False
