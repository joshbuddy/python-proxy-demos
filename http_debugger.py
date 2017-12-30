import httptools
import asyncio
import logging
import traceback
import selectors
import hexdump

# this class will intercept an http request and print out the headers
class HeaderPrinter:
    def on_header(self, name, value):
        print(f"got a header with name {str(name)} ==> {value}")

async def pipe2(reader, writer):
    try:
        parser = httptools.HttpRequestParser(HeaderPrinter())
        while not reader.at_eof():
            buf = await reader.read(4096)
            hexdump.hexdump(buf)
            parser.feed_data(buf)
            writer.write(buf)
    finally:
        writer.close()


async def pipe(reader, writer):
    try:
        while not reader.at_eof():
            buf = await reader.read(4096)
            #print(buf)
            writer.write(buf)
    finally:
        writer.close()


class Proxy(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        self.remote_reader, self.remote_writer = await asyncio.open_connection(
            '127.0.0.1', 8889)

    def data_received(self, data):
        print('Data received: {!r}'.format(data.decode()))

    def connection_lost(self, exc):
        print('The server closed the connection')
        print('Stop the event loop')
        self.loop.stop()


async def handle_client(local_reader, local_writer):
    try:
        pipe_1 = pipe2(local_reader, remote_writer)
        pipe_2 = pipe(remote_reader, local_writer)
        await asyncio.gather(pipe_1, pipe_2)
    except Exception as e:
        traceback.print_stack()

    finally:
        local_writer.close()


# Create the server
loop = asyncio.get_event_loop()
coro = asyncio.start_server(handle_client, '127.0.0.1', 8888)
server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
