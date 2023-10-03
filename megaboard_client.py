import datetime
import copy

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
        print(f"sign: [{string_sign_temp}]")
        print(f"by: [{secret}]")
        signature = hashlib.sha256(string_sign_temp.encode('utf-8')).hexdigest().upper()
        print(f"signature:{signature}")
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
        return requests.post(url, data=params, headers=headers)
