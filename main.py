from megaboard_client import MegaboardClient

access_key = "0uz4X3638ogYKuHZmRrL"
secret = "XjgBAUb4lo1t6xey7d5NdDgwaBM2iOXngQnWzgQQ"

if __name__ == '__main__':
    client = MegaboardClient(access_key, secret)
    res = client.get_server_time()
    print(res)
