import redis
import json

redis_client = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True
)

def cache_get(key):
    data = redis_client.get(key)
    return json.loads(data) if data else None

def cache_set(key, value, ttl=3600):
    redis_client.setex(key, ttl, json.dumps(value))