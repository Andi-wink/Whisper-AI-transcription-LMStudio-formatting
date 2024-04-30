import openllm
client = openllm.client.HTTPClient('http://localclient:3000')
response = client.query("Tell me a German joke")

print(response)


