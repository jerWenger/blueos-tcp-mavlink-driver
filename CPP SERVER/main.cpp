#include <iostream>
#include <string>
#include <random>
#include <thread>
#include <boost/asio.hpp>

using boost::asio::ip::tcp;

const unsigned short LOCAL_PORT = 9090;

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
    try
    {
        boost::asio::io_context io_context;
        tcp::acceptor acceptor(io_context, tcp::endpoint(tcp::v4(), LOCAL_PORT));

        std::cout << "Server is ready and listening on port " << LOCAL_PORT << "..." << std::endl;

        tcp::socket socket(io_context);
        acceptor.accept(socket);
        std::cout << "Connection accepted." << std::endl;

        std::thread t(handle, std::move(socket));
        t.join();
    }
    catch (const std::exception &e)
    {
        std::cerr << "Exception: " << e.what() << std::endl;
    }
}

int main()
{
    std::cout << "Server is ready..." << std::endl;
    receive();
    return 0;
}
