from iamai.engine import RuleEngine, Message
from iamai.mapper import Mapper

engine = RuleEngine()

engine.load_plugin('_plugin')

input_data = {
    "user": {
        "name": "John Doe",
        "email": "john.doe@example.com"
    },
    "details": {
        "age": 30,
        "location": "New York"
    }
}

message = Message('approve')
engine.execute('start', message)

mapper = Mapper('config.yml')
mapped_data = mapper.map(input_data)
print(mapped_data)