from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
from paillier import PaillierEncryptorFloat, PaillierText
from paillier.extra import squared_euclidian_oneside


class Recognizer:
    def __init__(self, img_size=150, precision=600):
        self.mtcnn = MTCNN(image_size=img_size)
        self.resnet = InceptionResnetV1(pretrained="vggface2").eval()
        self.precision = precision

    def _get_encodings(self, path):
        img = Image.open(path)
        img_cropped = self.mtcnn(img)
        embeddings = self.resnet(img_cropped.unsqueeze(0))

        return embeddings

    def get_crypt_encodings(self, path, pkey):
        pe = PaillierEncryptorFloat(precision=self.precision)
        pe.public_key = pkey

        encodings = self._get_encodings(path).detach().numpy()
        enc_sum = pe.encrypt(sum([p * p for p in encodings[0]]))
        return [pe.encrypt(val) for val in encodings[0]], enc_sum

    def compare(self, path, target_sum, target_embs, pkey):
        pe = PaillierEncryptorFloat(precision=self.precision)
        pe.public_key = pkey

        target_sum = PaillierText(target_sum, pkey[0], pe._precision_num)
        target_embs = [
            PaillierText(emb, pkey[0], pe._precision_num) for emb in target_embs
        ]

        encodings = self._get_encodings(path).detach().numpy()
        return squared_euclidian_oneside(pe, encodings[0], target_sum, target_embs)


global_rec = Recognizer()
