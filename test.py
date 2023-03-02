import openai
openai.api_key = "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"

completion = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "user", "content": "你好!"}
  ]
)

print(completion.choices[0].message)
