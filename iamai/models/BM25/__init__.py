import math
from collections import Counter

__all__ = ["BM25"]


class BM25:
    def __init__(self, documents):
        self.documents = documents
        self.N = len(documents)
        self.avgdl = sum(len(doc) for doc in documents) / self.N
        self.freqs = []
        self.idf = {}
        self.k1 = 1.5
        self.b = 0.75
        self.initialize()

    def initialize(self):
        for doc in self.documents:
            freq = Counter(doc)
            self.freqs.append(freq)
            for word in freq:
                if word not in self.idf:
                    df = sum(1 for document in self.documents if word in document)
                    self.idf[word] = math.log((self.N - df + 0.5) / (df + 0.5))

    def score(self, query):
        scores = []
        query_freq = Counter(query)
        query_words = set(query)
        for i in range(self.N):
            score = 0
            doc_len = len(self.documents[i])
            for word in query_words:
                if word in self.freqs[i]:
                    idf = self.idf[word]
                    tf = (
                        self.freqs[i][word]
                        * (self.k1 + 1)
                        / (
                            self.freqs[i][word]
                            + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                        )
                    )
                    score += idf * tf * query_freq[word]
            scores.append(score)
        return scores

    def search_top_k(self, query, k=5):
        scores = self.score(query)
        results = []
        for i, word in enumerate(query):
            sub_query = query[i:]
            sub_scores = self.score(sub_query)
            sub_top_k_indices = sorted(
                range(len(sub_scores)), key=lambda i: sub_scores[i], reverse=True
            )[:k]
            for j in sub_top_k_indices:
                result = self.documents[j].copy()
                result.extend(sub_query[len(result) :])
                results.append(result)
            if len(results) >= k:
                break
        return results[:k]

    def get_score(self, query):
        scores = self.score(query)
        return max(scores) if scores else 0.0
