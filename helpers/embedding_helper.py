from sentence_transformers import SentenceTransformer


model = SentenceTransformer("intfloat/multilingual-e5-small")

def embedd_data(data: dict):
    embeddings = model.encode(data, batch_size=64)
    return embeddings.shape


