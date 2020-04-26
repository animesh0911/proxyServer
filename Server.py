import socket
import threading
import json

class Server:
    def __init__(self):
        self.serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #using IPv4 addresses and TCP
        self.serverSocket.bind(('127.0.0.1',9000))
        self.serverSocket.listen(10)
    
    def isHostAllowed(self,conn,addr):
        file = open("lists.json","r")
        lists = json.load(file)
        for client in lists["blocked_clients"]:
            if(client == addr[0]):
                return False
        return True

    def isWebsiteAllowed(self, webserver):
        file = open("lists.json","r")
        lists = json.load(file)
        for website in lists["blocked_websites"]:
            if(website == webserver):
                return False
        return True

    def connectToClient(self):
        print("Waiting for clients")
        while True:
            conn,client_addr = self.serverSocket.accept()
            if(not self.isHostAllowed(conn,client_addr)):
                conn.close()
                continue
            clientThread = threading.Thread(target=self.handleClient,args=(conn,client_addr))
            clientThread.start()

    def handleClient(self,conn,client_addr):
        request = conn.recv(2048)
        first_line=request.split(b'\n')[0]
        url = first_line.split(b' ')[1]
        isHTTPS = first_line.split(b' ')[0]
        (webserver,port) = self.getWebServerPort(url)
        if(not self.isWebsiteAllowed(str(webserver))):
            conn.close()
        print(webserver)
        #print(port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        if(isHTTPS == b'CONNECT'): # https request
            conn.send(b'HTTP/1.1 200 Connection established\r\nProxy-agent: Simple/0.1\r\n\r\n')
            ServerToClientThread = threading.Thread(target=self.forwardData,args=(s,conn))
            ServerToClientThread.start()
            self.forwardData(conn, s)
        else: # http request
            s.sendall(request)
            self.forwardData(s, conn)

    def forwardData(self, s, conn):
        while 1:   
            data = s.recv(2048)
            if (len(data) > 0):
                conn.sendall(data)
            else:
                break

    def getWebServerPort(self,url):
        http_pos = url.find(b"://") # find pos of ://
        if (http_pos==-1):
            temp = url
        else:
            temp = url[(http_pos+3):] # get the rest of url
        port_pos = temp.find(b":") # find the port pos (if any)
        webserver_pos = temp.find(b"/")
        if webserver_pos == -1:
            webserver_pos = len(temp)
        webserver = ""
        port = -1
        if (port_pos==-1 or webserver_pos < port_pos): 
            port = 80 #default
            webserver = temp[:webserver_pos] 
        else: # specific port 
            port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
            webserver = temp[:port_pos] 
        return webserver,port
        

if __name__ == "__main__":
    s = Server()
    s.connectToClient()
