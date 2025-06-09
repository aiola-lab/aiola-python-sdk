```python
from aiola_stt import AiolaSttClient, AiolaConfig, AiolaQueryParams

config = AiolaConfig(
    api_key="<API-KEY>",
    query_params=AiolaQueryParams(execution_id="<unique-execution-id>")
)
client = AiolaSttClient(config)
await client.connect(auto_record=True)
```