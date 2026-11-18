import json
from collections import Counter
from pathlib import Path
from math import sqrt

def features(text):
    compact = "".join(text.lower().split())
    return Counter(compact[i:i+2] for i in range(len(compact)-1))

def retrieve(query, limit=2):
    rules = json.loads(Path(__file__).with_name("rules.json").read_text(encoding="utf-8"))
    query_vector = features(query)
    def similarity(rule):
        vector = features(rule)
        dot = sum(count * query_vector[word] for word, count in vector.items())
        norm = sqrt(sum(v*v for v in vector.values()) * sum(v*v for v in query_vector.values()))
        return dot / norm if norm else 0
    return [rule for rule in sorted(rules, key=similarity, reverse=True) if similarity(rule)>0][:limit]
