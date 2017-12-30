import httptools
import asyncio
import logging
import traceback
import selectors
import hexdump
import dnslib

class ProxyClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, data, proxy_transport, proxy_addr):
        self.data = data
        self.proxy_transport = proxy_transport
        self.proxy_addr = proxy_addr

    def connection_made(self, transport):
        self.transport = transport
        self.transport.sendto(self.data, ('8.8.4.4', 53))

    def datagram_received(self, data, addr):
        hexdump.hexdump(data)
        rec = dnslib.DNSRecord.parse(data)
        print(rec)
        self.proxy_transport.sendto(data, self.proxy_addr)

class ProxyProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        super().__init__()
    def connection_made(self, transport):
        self.transport = transport
    def datagram_received(self, data, addr):
        hexdump.hexdump(data)
        rec = dnslib.DNSRecord.parse(data)
        print(rec)
        asyncio.ensure_future(loop.create_datagram_endpoint(
                    lambda: ProxyClientProtocol(data, self.transport, addr),
                    remote_addr=('8.8.4.4', 53)))

loop = asyncio.get_event_loop()
t = loop.create_datagram_endpoint(ProxyProtocol,local_addr=('',9090))
loop.run_until_complete(t)
loop.run_forever()
