#include <iostream>
#include <string>
#include <random>
#include <thread>
#include <sock_ninja/sock_ninja.hpp>

const std::string REMOTE_HOST = "192.168.31.1";
const unsigned short REMOTE_PORT = 9090;

void broadcast(sock_ninja::tcp_socket &socket)
{
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> operation_dist(1, 2);
    std::uniform_int_distribution<> scalar_dist(0, 30);

    int operation = operation_dist(gen);
    int left_scalar = scalar_dist(gen);
    int right_scalar = scalar_dist(gen);

    std::string outgoing;
    if (operation == 1)
    {
        outgoing = std::to_string(1500 + 10 * left_scalar) + "," +
                   std::to_string(1500 + 10 * right_scalar);
    }
    else if (operation == 2)
    {
        outgoing = std::to_string(1500 - 10 * left_scalar) + "," +
                   std::to_string(1500 - 10 * right_scalar);
    }

    socket.send(outgoing + "\n");
}

void handle(sock_ninja::tcp_socket socket)
{
    try
    {
        std::string buffer;
        int counter = 1;
        int loops_since_start = 0;

        while (true)
        {
            std::string data = socket.recv_until("***");
            buffer += data;

            size_t pos;
            while ((pos = buffer.find("***")) != std::string::npos)
            {
                std::string messages = buffer.substr(0, pos);
                buffer.erase(0, pos + 3);

                if (counter == 4)
                {
                    std::cout << "Loop " << loops_since_start << std::endl;
                    counter = 0;
                    loops_since_start++;
                }

                // Generate and send a single response
                broadcast(socket);
                counter++;
            }
        }
    }
    catch (const std::exception &e)
    {
        std::cerr << "Exception: " << e.what() << std::endl;
        socket.close();
    }
}

void receive()
{
    sock_ninja::tcp_socket socket;
    socket.connect(REMOTE_HOST, REMOTE_PORT);

    std::cout << "Connected with " << REMOTE_HOST << std::endl;

    std::thread t(handle, std::move(socket));
    t.detach();
}

int main()
{
    std::cout << "Server is ready..." << std::endl;
    receive();
    return 0;
}
