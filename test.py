from flask import Flask     #导入Flask模块
from webhook import Webhook

#创建Flask的实例对象
app = Flask(__name__)
webhook = Webhook(app)

#装饰器
@app.route('/')
#视图函数
def hello_world():
    return 'Hello World!'

@webhook.hook('star')
def on_star(data):
    print(data['action'])
    return data['action']
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)