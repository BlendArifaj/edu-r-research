from common.http import Peers
from common.settings import peer_urls

_peers: Peers | None = None


def set_peers(peers: Peers) -> None:
    global _peers
    _peers = peers


def get_peers() -> Peers:
    global _peers
    if _peers is None:
        _peers = Peers(urls=peer_urls())
    return _peers
