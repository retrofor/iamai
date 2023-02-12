from transformers import pipeline

classifier = pipeline('sentiment-analysis')
print(classifier('fuck off!'))
print(classifier('how dare u?'))
print(classifier('boring..'))
