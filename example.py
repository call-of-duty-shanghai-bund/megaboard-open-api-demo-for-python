from megaboard_client import MegaboardClient


def add_keypair_example(client: MegaboardClient):
    res = client.add_keypair("TestUser", "okx", "okx-mainnet",
                             "b0732478-xxxx-xxxx-xxxx-680f87c23e3c",
                             "83xxxxxx0C021B87852",
                             "ThePassphrase123=")
    print(res)


def remove_keypair_example(client: MegaboardClient):
    res = client.remove_keypair("TestUser", "okx", "okx-mainnet")
    print(res)


def get_ip_whitelist_example(client: MegaboardClient):
    res = client.get_ip_whitelist("TestUser")
    print(res)


def place_ubase_market_order_example(client: MegaboardClient):
    res = client.place_ubase_market_order("TestUser", "binance-mainnet", "binance", "spot",
                                          "AXS", "LONG", 3, 0.03, 0.06)
    print(res)


def place_ubase_market_order_with_trailing_stop_example(client: MegaboardClient):
    res = client.place_ubase_market_order_with_trailing_stop("TestUser", "binance-mainnet", "binance", "perpetual",
                                                             "ETH", "LONG", 0.278, 0.03)
    print(res)
