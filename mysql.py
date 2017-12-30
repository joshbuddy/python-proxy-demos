import httptools
import asyncio
import logging
import traceback
import selectors
import hexdump
import struct
from pymysql import connections

#selector = selectors.SelectSelector()
#loop = asyncio.SelectorEventLoop(selector)
#asyncio.set_event_loop(loop)

async def pipe(reader, writer):
    try:
        while not reader.at_eof():
            msg = bytearray()

            buf = await reader.read(4096)
            msg.extend(buf)

            btrl, btrh, packet_number = struct.unpack('<HBB', msg[0:4])
            bytes_to_read = btrl + (btrh << 16)

            while len(msg) <= bytes_to_read:
                buf = await reader.read(4096)
                msg.extend(buf)
            hexdump.hexdump(msg)
            packet = connections.MysqlPacket(msg, 'utf8')
            packet.dump()
            print(packet)

            writer.write(msg)
        writer.close()
    except Exception as e:
        print(e)
        traceback.print_stack()


async def handle_client(local_reader, local_writer):
    try:
        remote_reader, remote_writer = await asyncio.open_connection(
            '127.0.0.1', 3306)
        pipe_1 = pipe(local_reader, remote_writer)
        pipe_2 = pipe(remote_reader, local_writer)
        await asyncio.gather(pipe_1, pipe_2)
    except Exception as e:
        traceback.print_stack()

    finally:
        local_writer.close()


# Create the server
loop = asyncio.get_event_loop()
coro = asyncio.start_server(handle_client, '127.0.0.1', 33306)
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
