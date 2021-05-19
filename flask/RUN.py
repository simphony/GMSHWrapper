from osp.wrappers.gmsh_wrapper.gmsh_session import (
    GMSHSession
)
from osp.core.session.transport.transport_session_server import \
    TransportSessionServer


def run_session(host, port):
    server = TransportSessionServer(GMSHSession, host, port)
    server.startListening()


if __name__ == '__main__':

    run_session("0.0.0.0", 7000)
