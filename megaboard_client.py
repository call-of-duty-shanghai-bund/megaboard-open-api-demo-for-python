import asyncio
import datetime
import copy
import json
from typing import Literal

import requests
import hashlib
import uuid

import websockets


class MegaboardClient:

    def __init__(self, access_key: str, secret: str, http_host: str = "https://api.megaboard.biz",
                 websocket_host="wss://api.megaboard.biz"):
        self.access_key = access_key
        self.secret = secret
        self.http_host = http_host
        self.websocket_host = websocket_host

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

    async def _ping_pong_task(self, websocket, sid):
        while True:
            ping_message = {
                "timestamp": int(datetime.datetime.now().timestamp() * 1000),
                "type": "ping",
                "sid": sid,
                "mid": str(uuid.uuid4()),
                "data": "ping",
                "version": "2.0"
            }
            await websocket.send(json.dumps(ping_message))
            print(f"Send Ping Frame:{ping_message}")
            await asyncio.sleep(5)  # Send a ping every 5 seconds

    async def _listen_task(self, websocket):
        try:
            while True:
                response = json.loads(await websocket.recv())
                if response.get("type") == "pong":
                    print(f"Received Pong Frame:{response}")
                else:
                    print(f"Received Data Message: {response}")
        except websockets.ConnectionClosed:
            print("Connection closed")

    async def create_connection(self, path: str, params=None):
        if params is None:
            params = {}

        url = self.websocket_host + path
        headers = self._generate_headers_for_auth(params)

        # 构造warmup message，完成鉴权&参数传递
        warmup_message = {
            "timestamp": int(datetime.datetime.now().timestamp() * 1000),
            "type": "warmup",
            "headers": headers,
            "data": params,
            "mid": str(uuid.uuid4()),
            "version": "2.0"
        }

        async with websockets.connect(url) as websocket:

            await websocket.send(json.dumps(warmup_message))
            print(f"Send Warmup Message:{warmup_message}")

            ack_response = json.loads(await websocket.recv())
            if ack_response.get("type") == "warmup" and ack_response.get("data") == "warmup success":
                print(f"ACK Warmup Message:{ack_response}")
                sid = ack_response["sid"]

                ping_pong_task = asyncio.create_task(self._ping_pong_task(websocket, sid))
                listen_task = asyncio.create_task(self._listen_task(websocket))

                await asyncio.gather(ping_pong_task, listen_task)
            else:
                print(f"Warmup failed:{ack_response}")

    def get(self, path: str, params=None):
        if params is None:
            params = {}

        url = self.http_host + path
        headers = self._generate_headers_for_auth(params)
        return requests.get(url, params=params, headers=headers).json()

    def post(self, path: str, params=None):
        if params is None:
            params = {}

        url = self.http_host + path
        headers = self._generate_headers_for_auth(params)
        return requests.post(url, data=params, headers=headers).json()

    def get_server_time(self):
        return self.get("/api/v1/time")

    def register_user(self, username: str):
        params = {
            "username": username
        }
        return self.post("/api/v1/user/register", params)

    def remove_user(self, username: str):
        params = {
            "username": username
        }
        return self.post("/api/v1/user/remove", params)

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

    def place_ubase_market_order_stateless(self, username: str, apikey: str, apisecret: str,
                                           exchange: Literal["binance", "okx", "bybit"],
                                           market: Literal["spot", "perpetual"], coin: str,
                                           side: Literal["LONG", "SHORT"], amount: float, tp_rate: float = None,
                                           sl_rate: float = None, passphrase: str = None):
        params = {
            "username": username,
            "apikey": apikey,
            "apisecret": apisecret,
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
        if passphrase:
            params.update({"passphrase": passphrase})
        return self.post("/api/v1/stateless/order/market/ubase", params)

    def place_ubase_market_order_with_trailing_stop_stateless(self, username: str, apikey: str, apisecret: str,
                                                              exchange: Literal["binance", "okx", "bybit"],
                                                              market: Literal["spot", "perpetual"], coin: str,
                                                              side: Literal["LONG", "SHORT"], amount: float,
                                                              pullback_rate: float, passphrase: str = None):
        params = {
            "username": username,
            "apikey": apikey,
            "apisecret": apisecret,
            "exchange": exchange,
            "market": market,
            "coin": coin,
            "side": side,
            "amount": amount,
            "pullback": pullback_rate
        }
        if passphrase:
            params.update({"passphrase": passphrase})
        return self.post("/api/v1/stateless/order/market/ubase/trailing-stop", params)

    # please run with asyncio.run
    async def subscribe_positions_stateless(self, username: str, apikey: str, apisecret: str, exchange: str,
                                            market: str, passphrase: str = None):
        params = {
            "username": username,
            "apikey": apikey,
            "apisecret": apisecret,
            "exchange": exchange,
            "market": market,
        }
        if passphrase:
            params.update({"passphrase": passphrase})
        await self.create_connection("/api/v1/ws/stateless/positions", params)

    async def subscribe_balance_stateless(self, username: str, apikey: str, apisecret: str, exchange: str,
                                          market: str, passphrase: str = None):
        params = {
            "username": username,
            "apikey": apikey,
            "apisecret": apisecret,
            "exchange": exchange,
            "market": market,
        }
        if passphrase:
            params.update({"passphrase": passphrase})
        await self.create_connection("/api/v1/ws/stateless/balance", params)
