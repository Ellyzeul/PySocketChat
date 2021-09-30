from server import create_server
from threading import Thread, get_ident
from tests import active_threads_test
import os


def listen_client(addr, connected_clients):
    """Função para escutar as mensagens enviadas pelos clientes.
    
    Ao receber um dicionário com todos os clientes conectados e o endereço
    correspondente ao cliente que será escutado, ficará escutando por 
    mensagens desse cliente e ao receber enviará a todos os outros."""

    ip_port = f"{addr[0]}:{addr[1]}"
    client = connected_clients[ip_port]["socket"]

    while True:
        msg = client.recv(4096).decode("utf-8")
        spl_msg = msg.split('> ', 1)

        if spl_msg[0][0] == '\\': # Se o começo da mensagem, que geralmente é o display com username começar com \ significa que não é uma mensagem comum de usuário e sim uma mensagem do cliente dizendo qual o nome de usuário do novo usuário
            connected_clients[ip_port]["username"] = spl_msg[0][1:]
            continue

        if spl_msg[1] == "\quit": # Em caso da mensagem ser de desconexão do cliente
            to_pop = connected_clients.pop(ip_port) # Retirando cliente da lista dos clientes conectados
            to_pop["socket"].close()
            return

        possible_user = spl_msg[1].split(' ', 1)[0]
        if possible_user[-1] == '%':    # Aqui se faz o tratamento de marcadores, pois um usuário pode marcar um usuário específico para enviar mensagem usando 'user% '.
            jump = False
            for connection in connected_clients.items(): # Visitando cada cliente conectado para ver qual tem o nome de usuário correspondente ao marcado
                if connection[1]['username'] == possible_user[:-1]:
                    connection[1]['socket'].send(bytes(
                        f"({get_ident()}) {msg.split(' ',1)[0]}{msg.split('%',1)[1]}", "utf-8"  # Enviando a mensagem removendo o marcador
                    ))
                    jump = True
            if jump: continue

        for connection in connected_clients.items(): # Visitando cada cliente conectado para enviar a mensagem recebida
            if connection[0] != ip_port: # Caso o cliente seja quem enviou a mensagem, ele não a receberá, para não gerar duplicação
                connection[1]["socket"].send(bytes(f"({get_ident()}) {msg}", "utf-8"))

def run():
    """Função para instanciar servidor e ficar escutando requisição do cliente"""

    server = create_server()
    connected_clients = {} # Inicializando lista de clientes conectados (como dict para acessar os índices como ip e porta do cliente em uma string, por exemplo: connected_clients["127.0.0.1:5000"])
    
    try:
        while True:
            connected_socket, address = server.accept() # Aceitando conexão do cliente

            connected_clients[f"{address[0]}:{address[1]}"] = {'socket': connected_socket} # Adicionando à lista com todos os clientes conectados
            print(f"client from {address[0]}:{address[1]} established")

            t = Thread(
                target=listen_client, 
                args=(address, connected_clients,), 
                daemon=True
            )
            t.start() # Iniciando uma thread para ficar escutando as mensagens enviadas por esse novo cliente

    except KeyboardInterrupt: # Em caso de derrubar o servidor com Ctrl+C
        for client in list(connected_clients.values()):
            client['socket'].close()
        print('\n\nShutting down..')
        exit()


run()