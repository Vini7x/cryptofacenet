import configparser
import os
from paillier import PaillierEncryptorFloat, PaillierText


class Owner:
    def __init__(self, owner_name, encryptor):
        self.name = owner_name
        self.encryptor = encryptor

    @staticmethod
    def create(name, precision=600):
        encryptor = PaillierEncryptorFloat(precision=precision)
        return Owner(name, encryptor)

    @property
    def public_key(self):
        return self.encryptor.public_key

    def save(self, path):
        config = configparser.ConfigParser()
        config["OWNER"] = {}
        config["OWNER"]["name"] = self.name
        config["OWNER"]["p"] = str(self.encryptor.p)
        config["OWNER"]["q"] = str(self.encryptor.q)
        config["OWNER"]["public_key1"] = str(self.encryptor.public_key[0])
        config["OWNER"]["public_key2"] = str(self.encryptor.public_key[1])
        config["OWNER"]["private_key1"] = str(self.encryptor.private_key[0])
        config["OWNER"]["private_key2"] = str(self.encryptor.private_key[1])
        with open(path, "w") as f:
            config.write(f)

    @staticmethod
    def load(path):
        if not os.path.exists(path):
            raise FileNotFoundError("config does not exist")

        config = configparser.ConfigParser()
        config.read(path)

        owner_data = config["OWNER"]
        owner = Owner.create(owner_data["name"])
        owner.encryptor.p = int(owner_data["p"])
        owner.encryptor.q = int(owner_data["q"])
        owner.encryptor.public_key = (
            int(owner_data["public_key1"]),
            int(owner_data["public_key2"]),
        )
        owner.encryptor.private_key = (
            int(owner_data["private_key1"]),
            int(owner_data["private_key2"]),
        )

        return owner

    def decrypt(self, data):
        return self.encryptor.decrypt(
            PaillierText(
                data, self.encryptor.public_key[0], self.encryptor._precision_num
            )
        )
