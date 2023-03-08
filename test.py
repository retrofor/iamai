import requests

API_URL = "https://api-inference.huggingface.co/models/facebook/fastspeech2-en-ljspeech"
headers = {"Authorization": "Bearer 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"}

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()
	
output = query({
	"inputs": "The answer to the universe is 42",
})
print(output)