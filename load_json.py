import json
class key_and_pass:
    def __init__(self,oauth_json,sql_json):
        with open(oauth_json) as file:
            self.oauth_json = json.load(file)
        with open(sql_json) as file:
            self.sql_json = json.load(file)