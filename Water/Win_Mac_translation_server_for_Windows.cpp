#include <iostream>
#include <zmq.h>
#include <ws2tcpip.h>
#include <winsock2.h>
#include <stdio.h>
#include <sstream>
#include <vector> // Include vector

int main() {
    // Initialize Winsock
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed" << std::endl;
        return 1;
    }

    void *context = zmq_ctx_new();

    // Create subscriber sockets
    void *sub_sock_SD = zmq_socket(context, ZMQ_SUB);
    zmq_bind(sub_sock_SD, "tcp://*:666");
    zmq_setsockopt(sub_sock_SD, ZMQ_SUBSCRIBE, "", 0);

    void *sub_sock_MM = zmq_socket(context, ZMQ_SUB);
    zmq_bind(sub_sock_MM, "tcp://*:667");
    zmq_setsockopt(sub_sock_MM, ZMQ_SUBSCRIBE, "", 0);

    // Polling items
    zmq_pollitem_t items[] = {
        { sub_sock_SD, 0, ZMQ_POLLIN, 0 },
        { sub_sock_MM, 0, ZMQ_POLLIN, 0 },
    };

    std::string m_multicastaddress = "239.192.1.1";
    int m_multicastport_SD = 5000;
    int m_multicastport_MM = 5000;

    // Setup socket for SD
    SOCKET sock_SD = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock_SD == INVALID_SOCKET) {
        std::cerr << "Failed to create socket for SD" << std::endl;
        WSACleanup();
        return 1;
    }

    // Set socket options for SD
    struct linger l;
    l.l_onoff = 0;
    l.l_linger = 0;
    setsockopt(sock_SD, SOL_SOCKET, SO_LINGER, (char*)&l, sizeof(l));

    sockaddr_in addr_SD;
    ZeroMemory(&addr_SD, sizeof(addr_SD));
    addr_SD.sin_family = AF_INET;
    addr_SD.sin_addr.s_addr = htonl(INADDR_ANY);
    addr_SD.sin_port = htons(m_multicastport_SD);

    // Send address for SD
    addr_SD.sin_addr.s_addr = inet_addr(m_multicastaddress.c_str());

    // Setup socket for MM
    SOCKET sock_MM = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock_MM == INVALID_SOCKET) {
        std::cerr << "Failed to create socket for MM" << std::endl;
        closesocket(sock_SD);
        WSACleanup();
        return 1;
    }

    // Set socket options for MM
    struct linger l_MM;
    l_MM.l_onoff = 0;
    l_MM.l_linger = 0;
    setsockopt(sock_MM, SOL_SOCKET, SO_LINGER, (char*)&l_MM, sizeof(l_MM));

    sockaddr_in addr_MM;
    ZeroMemory(&addr_MM, sizeof(addr_MM));
    addr_MM.sin_family = AF_INET;
    addr_MM.sin_addr.s_addr = htonl(INADDR_ANY);
    addr_MM.sin_port = htons(m_multicastport_MM);

    // Send address for MM
    addr_MM.sin_addr.s_addr = inet_addr(m_multicastaddress.c_str());

    while (true) {
        zmq_poll(items, 2, -1);

        if (items[0].revents & ZMQ_POLLIN) {
            zmq_msg_t received_SD;
            zmq_msg_init(&received_SD);
            zmq_msg_recv(&received_SD, sub_sock_SD, 0);

            std::string pubmessage(static_cast<char*>(zmq_msg_data(&received_SD)), zmq_msg_size(&received_SD)); // Convert message to string

            // Use std::vector to create a dynamically sized buffer
            std::vector<char> message(pubmessage.length() + 1);
            snprintf(message.data(), message.size(), "%s", pubmessage.c_str());
            sendto(sock_SD, message.data(), pubmessage.length(), 0, (struct sockaddr*)&addr_SD, sizeof(addr_SD));

            zmq_msg_close(&received_SD);
        }

        if (items[1].revents & ZMQ_POLLIN) {
            zmq_msg_t received_MM;
            zmq_msg_init(&received_MM);
            zmq_msg_recv(&received_MM, sub_sock_MM, 0);

            std::string pubmessage(static_cast<char*>(zmq_msg_data(&received_MM)), zmq_msg_size(&received_MM)); // Convert message to string

            // Use std::vector to create a dynamically sized buffer
            std::vector<char> message(pubmessage.length() + 1);
            snprintf(message.data(), message.size(), "%s", pubmessage.c_str());
            sendto(sock_MM, message.data(), pubmessage.length(), 0, (struct sockaddr*)&addr_MM, sizeof(addr_MM));

            zmq_msg_close(&received_MM);
        }
    }

    // Cleanup
    zmq_close(sub_sock_SD);
    zmq_close(sub_sock_MM);
    zmq_ctx_destroy(context);
    closesocket(sock_SD);
    closesocket(sock_MM);
    WSACleanup();
    return 0;
}
