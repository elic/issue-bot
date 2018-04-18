import json

class Issue:

    def __init__(self, init_string=None):
        if init_string:
            self.fields = json.loads(init_string)['fields']
        else:
            self.fields = {'Title':'',
                           'Category': '',
                           'Description': '',
                           'Status':'pending',
                           'Attachments':[]
                           }

    def set_title(self, message):
        self.fields['Title'] = message[6:].strip()

    def set_category(self, message):
        self.fields['Category'] = message[9:].strip()

    def append_description(self, message):
        if self.fields['Description'] == '':
            self.fields['Description'] = message
        else:
            self.fields['Description'] = self.fields['Description'] + '\n' + message

    def append_attachment(self, attachment_url):
        self.fields['Attachments'].append({'url': attachment_url})

    def to_json_string(self):
        return json.dumps(self.__dict__)

    def is_empty(self):
        return len(self.fields['Title']) == 0 and len(self.fields['Category']) == 0 and \
               len(self.fields['Description']) == 0 and len(self.fields['Attachments']) == 0

def is_title(message):
    return message[:6].lower() == 'title:'

def is_category(message):
    return message[:9].lower() == 'category:'

def is_trigger_summit(message):
    return message[:4] == '===='
