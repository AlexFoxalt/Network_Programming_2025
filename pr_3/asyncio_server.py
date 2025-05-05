import asyncio
from settings import HOST, PORT


async def handle_client(reader, writer):
    client_addr = writer.get_extra_info("peername")
    print(f"New connection from {client_addr}")

    welcome_msg = "Welcome to the asyncio chat server!"
    writer.write(welcome_msg.encode("utf-8"))
    await writer.drain()

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            message = data.decode("utf-8")
            print(f"Message from {client_addr}: {message}")

    except ConnectionResetError:
        print(f"Connection reset by {client_addr}")
    except Exception as e:
        print(f"Error handling client {client_addr}: {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Connection with {client_addr} closed")


async def main():
    server = await asyncio.start_server(
        handle_client, HOST, PORT, reuse_address=True
    )

    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
