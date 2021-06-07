import salt.utils.minions
import salt.utils.network
from tests.support.mock import patch


def test_connected_ids():
    """
    test ckminion connected_ids when
    local_port_tcp returns 127.0.0.1
    """
    opts = {"publish_port": 4505, "minion_data_cache": True}
    minion = "minion"
    ips = {"203.0.113.1", "203.0.113.2"}
    mdata = {"grains": {"ipv4": ips, "ipv6": []}}
    patch_ip_addrs = patch("salt.utils.network.local_port_tcp", return_value=ips)
    patch_net = patch("salt.utils.network.local_port_tcp", return_value={"127.0.0.1"})
    patch_list = patch("salt.cache.Cache.list", return_value=[minion])
    patch_fetch = patch("salt.cache.Cache.fetch", return_value=mdata)

    ckminions = salt.utils.minions.CkMinions(opts)
    with patch_net, patch_ip_addrs, patch_list, patch_fetch:
        ret = ckminions.connected_ids()
        assert ret == {minion}
