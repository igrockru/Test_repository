#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
import time



class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport


    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)
        decoded = data.decode()
        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                try_login = decoded.replace("login:", "").replace("\r\n", "")
                if try_login not in [user.login for user in self.server.clients]:
                    self.login = try_login
                    self.transport.write(
                        f"Привет, {self.login}!\r\n".encode()
                    )
                    self.send_history()
                else:
                    self.transport.write(f"Логин {try_login} занят, попробуйте другой\r\n".encode())
                    time.sleep(1.5)
                    self.transport.close()

            else:
                self.transport.write("Некорректный логин\r\n".encode())

    def send_history(self):
        for message in self.server.history:
            self.transport.write(message.encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент ушел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        if len(self.server.history) >= 10:
            del (self.server.history[0])
        self.server.history.append(message)
        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list
    history: list


    def __init__(self):
        self.clients = []
        self.login_list = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
