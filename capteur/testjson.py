import json


config = {'frq_start': 400*10**6, 'frq_end': 420*10**6, 'sensibilite': 10}

with open('config.json', 'w') as f:
    json.dump(config, f)


with open('config.json') as f:
    x = json.load(f)
    print(x['frq_start'])
    print(x['frq_end'])
    print(x['sensibilite'])

