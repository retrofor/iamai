from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_dir = r'D:\models\bert-base-uncased'
tokenizer = AutoTokenizer.from_pretrained(model_dir)
model = AutoModelForSequenceClassification.from_pretrained(model_dir)

# 定义起始文本序列
input_ids = tokenizer.encode("The cat", return_tensors='pt')

# 生成文本
sample_outputs = model.generate(input_ids, do_sample=True, max_length=50, top_k=50)
generated_text = tokenizer.decode(sample_outputs[0], skip_special_tokens=True)

# 输出生成的文本
print(generated_text)