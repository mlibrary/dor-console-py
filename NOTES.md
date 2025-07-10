## Using httpx yields a 403

```
    headers = {'User-Agent': USER_AGENT, 'Connection': 'close'}
    with httpx.Client(headers=headers) as client:
        del client.headers['accept-encoding']
        r = client.get(collection_url)
        console.print(f":cheese_wedge: {collid} :: {r.status_code} :: {collection_url}")
        print(r.text)
```

