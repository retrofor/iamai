from iamai.config import load_config

class Mapper:
    def __init__(self, config_file):
        self.config = load_config(config_file)
        self.rules = self.config.get('rules', [])

    def map(self, input_data):
        output_data = {}
        for key, value in input_data.items():
            self._set_value(output_data, key, value)
        return output_data

    def _get_value(self, data, path):
        keys = path.split('.')
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            elif isinstance(data, list):
                data = data[int(key)] if key.isdigit() else None
            if data is None:
                break
        return data

    def _set_value(self, data, path, value):
        keys = path.split('.')
        for key in keys[:-1]:
            if key.isdigit():
                key = int(key)
                while len(data) <= key:
                    data.append({})
                data = data[key]
            else:
                if key not in data:
                    data[key] = {}
                data = data[key]
        last_key = keys[-1]
        if last_key.isdigit():
            last_key = int(last_key)
            while len(data) <= last_key:
                data.append(None)
            data[last_key] = value
        else:
            data[last_key] = value

if __name__ == "__main__":
    mapper = Mapper('config.yml')
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
    mapped_data = mapper.map(input_data)
    print(mapped_data)