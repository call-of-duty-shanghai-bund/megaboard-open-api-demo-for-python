import datetime
import copy
from typing import Literal

import requests
import hashlib
import uuid


class MegaboardClient:

    def __init__(self, access_key: str, secret: str, host: str = "https://api.megaboard.biz"):
        self.access_key = access_key
        self.secret = secret
        self.host = host

    @staticmethod
    def _generate_signature(params: dict[str, str], access_key: str, secret: str, timestamp: str,
                            nonce: str) -> str:
        """
        Compute the signature for the provided parameters using the specified SecretKey.
        This implementation uses SHA-256 for added security.

        Args:
            params (Dict[str, str]): A dictionary of parameters used to compute the signature.
            secret (str): The SecretKey used to compute the signature.

        Returns:
            str: The computed signature.
        """
        params_for_sign = copy.deepcopy(params)
        params_for_sign.update({"timestamp": timestamp, "nonce": nonce, "accessKey": access_key})
        # Sort the parameters by key and concatenate them into a string
        string_a = "&".join([f"{k}={v}" for k, v in sorted(params_for_sign.items())])

        # Concatenate the SecretKey to the parameters string
        string_sign_temp = string_a + secret

        # Compute and return the SHA-256 hash of the concatenated string, converted to uppercase
        # print(f"sign: [{string_sign_temp}]")
        # print(f"by: [{secret}]")
        signature = hashlib.sha256(string_sign_temp.encode('utf-8')).hexdigest().upper()
        # print(f"signature:{signature}")
        return signature

    def _generate_headers_for_auth(self, params: dict) -> dict:
        timestamp_by_ms = str(int(datetime.datetime.now().timestamp() * pow(10, 3)))
        nonce = str(uuid.uuid4())
        headers = {
            "timestamp": timestamp_by_ms,
            "nonce": nonce,
            "accessKey": self.access_key,
            "signature": self._generate_signature(params, self.access_key, self.secret, timestamp_by_ms, nonce)
        }
        return headers

    def get(self, path: str, params=None):
        if params is None:
            params = {}

        url = self.host + path
        headers = self._generate_headers_for_auth(params)
        return requests.get(url, params=params, headers=headers).json()

    def post(self, path: str, params=None):
        if params is None:
            params = {}

        url = self.host + path
        headers = self._generate_headers_for_auth(params)
        return requests.post(url, data=params, headers=headers).json()

    def get_server_time(self):
        return self.get("/api/v1/time")

    def add_keypair(self, username: str, exchange: str, account_name: str, apikey: str, secret: str,
                    passphrase: str = None):
        params = {
            "username": username,
            "exchange": exchange,
            "account_name": account_name,
            "apikey": apikey,
            "secret": secret
        }
        if passphrase:
            params.update({"passphrase": passphrase})
        return self.post("/api/v1/keypair", params)

    def remove_keypair(self, username: str, exchange: Literal["binance", "okx", "bybit"], account_name: str):
        params = {
            "username": username,
            "exchange": exchange,
            "account_name": account_name
        }
        return self.post("/api/v1/keypair/remove", params)

    def get_keypairs_info(self, username: str):
        params = {"username": username}
        return self.get("/api/v1/keypairs", params)

    def get_ip_whitelist(self, username: str):
        params = {"username": username}
        return self.get("/api/v1/ip/whitelist", params)

    def place_ubase_market_order(self, username: str, account_name: str, exchange: Literal["binance", "okx", "bybit"],
                                 market: Literal["spot", "perpetual"], coin: str,
                                 side: Literal["LONG", "SHORT"], amount: float, tp_rate: float = None,
                                 sl_rate: float = None):
        params = {
            "username": username,
            "account_name": account_name,
            "exchange": exchange,
            "market": market,
            "coin": coin,
            "side": side,
            "amount": amount
        }
        if tp_rate:
            params.update({"tp_rate": tp_rate})
        if sl_rate:
            params.update({"sl_rate": sl_rate})
        return self.post("/api/v1/order/market/ubase", params)

    def place_ubase_market_order_with_trailing_stop(self, username: str, account_name: str,
                                                    exchange: Literal["binance", "okx", "bybit"],
                                                    market: Literal["spot", "perpetual"], coin: str,
                                                    side: Literal["LONG", "SHORT"], amount: float,
                                                    pullback_rate: float):
        params = {
            "username": username,
            "account_name": account_name,
            "exchange": exchange,
            "market": market,
            "coin": coin,
            "side": side,
            "amount": amount,
            "pullback": pullback_rate
        }
        return self.post("/api/v1/order/market/ubase/trailing-stop", params)
