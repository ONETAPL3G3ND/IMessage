import grpc
from concurrent import futures
import time
import messenger_pb2
import messenger_pb2_grpc

class MessengerServicer(messenger_pb2_grpc.MessengerServicer):
    def __init__(self):
        self.users = {}
        self.logged_in_users = {}

    def SendMessage(self, request, context):
        if request.receiver in self.logged_in_users:
            chat_name = request.receiver
            chat = self.logged_in_users[chat_name].chats.get(request.sender, [])
            chat.append(request)
            self.logged_in_users[chat_name].chats[request.sender] = chat
            return messenger_pb2.Message(sender=request.sender, receiver=request.receiver, content=request.content)
        return messenger_pb2.Message()

    def GetChatHistory(self, request, context):
        chat_name = request.name
        if chat_name in self.logged_in_users:
            for message in self.logged_in_users[chat_name].messages:
                yield message
        else:
            yield messenger_pb2.Message(content="No chat history")

    def CreateChat(self, request, context):
        if request.username in self.users:
            if request.username not in self.logged_in_users:
                self.logged_in_users[request.username] = self.users[request.username]
                return messenger_pb2.Chat(name=request.username, messages=self.logged_in_users[request.username].messages)
            else:
                return messenger_pb2.Chat(name=request.username, messages=self.logged_in_users[request.username].messages)
        else:
            return messenger_pb2.Chat(name="", messages=[])

    def Login(self, request, context):
        if request.username in self.users and self.users[request.username].password == request.password:
            return messenger_pb2.LoginResponse(success=True)
        else:
            return messenger_pb2.LoginResponse(success=False, message="Invalid credentials")

    def Register(self, request, context):
        if request.username not in self.users:
            self.users[request.username] = messenger_pb2.UserState(password=request.password, chats={}, messages=[])
            return messenger_pb2.RegisterResponse(success=True)
        else:
            return messenger_pb2.RegisterResponse(success=False, message="Username already exists")

class UserState:
    def __init__(self, password, chats, messages):
        self.password = password
        self.chats = chats
        self.messages = messages

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messenger_pb2_grpc.add_MessengerServicer_to_server(MessengerServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
