#include <iostream>
#include <string>
#include <random>
#include <thread>
#include <boost/asio.hpp>

using boost::asio::ip::tcp;

const std::string REMOTE_HOST = "192.168.31.1";
const unsigned short REMOTE_PORT = 9090;

void broadcast(tcp::socket &socket)
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
        outgoing = "(" + std::to_string(1500 + 10 * left_scalar) + "," +
                   std::to_string(1500 + 10 * right_scalar) + ")";
    }
    else if (operation == 2)
    {
        outgoing = "(" + std::to_string(1500 - 10 * left_scalar) + "," +
                   std::to_string(1500 - 10 * right_scalar) + ")";
    }

    boost::asio::write(socket, boost::asio::buffer(outgoing));
}

void handle(tcp::socket socket)
{
    try
    {
        std::string buffer;
        int counter = 1;
        int loops_since_start = 0;
        boost::asio::streambuf receive_buffer;

        while (true)
        {
            boost::asio::read_until(socket, receive_buffer, "***");
            std::istream is(&receive_buffer);
            std::string data;
            std::getline(is, data);
            buffer += data;

            size_t pos;
            while ((pos = buffer.find("***")) != std::string::npos)
            {
                std::string messages = buffer.substr(0, pos);
                buffer.erase(0, pos + 3);

                if (counter == 10)
                {
                    std::cout << "Loop " << loops_since_start << std::endl;
                    std::cout << "Received: " << messages << std::endl;
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
    boost::asio::io_context io_context;
    tcp::resolver resolver(io_context);
    tcp::resolver::results_type endpoints = resolver.resolve(REMOTE_HOST, std::to_string(REMOTE_PORT));
    tcp::socket socket(io_context);
    boost::asio::connect(socket, endpoints);

    std::cout << "Connected with " << REMOTE_HOST << std::endl;

    std::thread t(handle, std::move(socket));
    t.join();
}

int main()
{
    std::cout << "Server is ready..." << std::endl;
    receive();
    return 0;
}
