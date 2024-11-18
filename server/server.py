import socket
import threading
import os
from tqdm import tqdm

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER,PORT)
FORMAT = 'utf-8'
DISCONNECT_MSG = "!DISCONNECT"
UPLOAD_MSG = "!UPLOAD"
LIST_MSG = "!LIST"
DOWNLOAD_MSG = "!DOWNLOAD"
DELETE_MSG = "!DELETE"

#semaphore for synch

max_downloads = 1
delete_flags = {}
delete_locks = {}
def create_semaphores(files, max_downloads):
    file_semaphores = {}
    for file in files:
        file_semaphores[file] = threading.BoundedSemaphore(value=max_downloads)
        delete_flags[file] = False
        delete_locks[file] = threading.Lock()
    return file_semaphores,delete_flags,delete_locks

cwd = os.getcwd()
filed = cwd + "/files"
filenames = os.listdir(filed)

semaphore_files,delete_flags,delete_locks = create_semaphores(filenames,max_downloads)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

class Client:
    def __init__(self,conn,addr):
        self.conn = conn
        self.addr = addr
        self.connected = True

    def upload(self):
    # Receive initial response to check if file is found
        response = self.conn.recv(128).decode(FORMAT)
        if "not found" in response:
            print(f"[THREAD {threading.current_thread().name}] File not found")
        else:
            print(f"[THREAD {threading.current_thread().name}] File found")

            # Receive and decode file size
            file_size = int(self.conn.recv(128).decode(FORMAT).strip())
            
            # Receive and decode file name
            file_name = self.conn.recv(128).decode(FORMAT).strip()
            print(f"Receiving file: {file_name}")

            # Set up the progress bar
            bar = tqdm(range(file_size), f"Receiving {file_name}", unit="B", unit_scale=True, unit_divisor=1024, dynamic_ncols=True, ncols=20)
            
            # Open the file for writing
            with open(f"files/{file_name}", "wb") as f:
                bytes_recv = 0
                while bytes_recv < file_size:
                    data = self.conn.recv(1024)
                    if not data:
                        break
                    f.write(data)
                    bytes_recv += len(data)
                    bar.update(len(data))
                bar.close()

            print("File downloaded successfully")

            # After successful upload, add delete flag, lock, and semaphore for the new file
            with threading.Lock():
                delete_flags[file_name] = False
                delete_locks[file_name] = threading.Lock()
                semaphore_files[file_name] = threading.BoundedSemaphore(value=max_downloads)

            print(f"Added delete flag, lock, and semaphore for new file: {file_name}")


    def download(self):
        file_length = self.conn.recv(HEADER).decode(FORMAT)
        file_name = self.conn.recv(int(file_length)).decode(FORMAT)

        cwd = os.getcwd()
        filed = os.path.join(cwd,"files")
        dirlist = os.listdir(filed)
        if file_name in dirlist:
            print(f"{file_name} found!")


            if delete_flags[file_name]:
                print(f"[THREAD {threading.current_thread().name}] Cannot download {file_name}, marked for deletion!")
                self.conn.send(f"Cannot download {file_name}, file is being deleted!".encode(FORMAT))
                return
        
            print(f"[THREAD {threading.current_thread().name}] Waiting to download {file_name}")
            semaphore_files[file_name].acquire()
            print(f"[THREAD {threading.current_thread().name}] Acquired semaphore for {file_name}")

            try:
                filePath = f"{filed}/{file_name}"
                with open(f"{filePath}","rb") as file:
                    file_size = str(os.stat(filePath).st_size)
                    file_size = file_size.encode(FORMAT)
                    file_size += b' ' * (128-len(file_size))
                    file_size = self.conn.send(file_size)
                    while True:
                        data = file.read(1024)
                        if not data:
                            break
                        self.conn.send(data)
            finally:
                semaphore_files[file_name].release()
                print(f"[THREAD {threading.current_thread().name}] Released semaphore for {file_name}")

        else:
            self.conn.send(f"File not found!".encode(FORMAT))
            print("File not found!")

    def listMsg(self):
        cwd = os.getcwd()
        filed = cwd + "/files"
        dirlist = os.listdir(filed)
        data = str(dirlist)
        data = data.encode(FORMAT)
        data += b' ' * (1024-len(data))
        self.conn.send(data)

    def delete(self):
        file_length = self.conn.recv(HEADER).decode(FORMAT)
        file_name = self.conn.recv(int(file_length)).decode(FORMAT)
        cwd = os.getcwd()
        filed = os.path.join(cwd,"files")
        dirlist = os.listdir(filed)
        if file_name in dirlist:
            print(f"{file_name} found")
            with delete_locks[file_name]:
                delete_flags[file_name] = True
                print(f"{file_name} marked for deletion. Waiting for ongoing downloads to finish...")
                for _ in range(max_downloads):
                    semaphore_files[file_name].acquire()

                os.remove(f"{filed}/{file_name}")
                print(f"{file_name} deleted!")
                self.conn.send(f"{file_name} deleted successfully!".encode(FORMAT))

                for _ in range(max_downloads):
                    semaphore_files[file_name].release()

            delete_flags[file_name] = False
        else:
            self.conn.send(f"{file_name} not found!".encode(FORMAT))
            print("File not found!")


    def commands(self):
        while self.connected:
            msg_length = self.conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = self.conn.recv(msg_length).decode(FORMAT)
                print(f"[{self.addr}] {msg}")
                if(msg==DISCONNECT_MSG):
                    self.connected = False
                elif(msg==UPLOAD_MSG):
                    self.upload()
                elif(msg==DOWNLOAD_MSG):
                    self.download()
                elif(msg==LIST_MSG):
                    self.listMsg()
                elif(msg==DELETE_MSG):
                    self.delete()


                    


def handle_client(conn,addr):
    print(f"NEW CONNECTION {addr} connected")
    x = Client(conn,addr)
    x.commands()
    conn.close()

def start():
    server.listen()
    print(f"[LISTENING] server is listening on {SERVER}")
    while True:
        conn,addr = server.accept()
        thread = threading.Thread(target=handle_client,args=(conn,addr))
        thread.start()
        
        print(f"[ACTIVE CONNECTIONS] {threading.active_count()-1}")


print("[STARTING] server is starting")
start()