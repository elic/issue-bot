import os
import json
import sys
import traceback
import requests
from flask import Flask
from flask import jsonify
from flask import request
from pymongo import MongoClient
from app.issue import Issue
from app.issue import is_title
from app.issue import is_trigger_summit
from app.issue import is_category

app = Flask(__name__)

HOST = 'https://issue-bot.herokuapp.com/'
LINE_API_URL = 'https://api.line.me/v2/bot/message/reply'
LINE_CONTENT_URL = 'https://api.line.me/v2/bot/message/'

MONGODB_URI = os.environ.get('MONGODB_URI', None)
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', None)
AIRTABEL_API_URL = os.environ.get('AIRTABEL_API_URL', None)
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY', None)
AIRTABEL_SHARED_URL = os.environ.get('AIRTABEL_SHARED_URL', None)

@app.route('/')
def hello():
    return 'Hello World!!'

@app.route('/bot/reply', methods=['POST'])
def webhook():
    try:
        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + LINE_CHANNEL_SECRET}
        for events in request.json['events']:
            if events['message']['type'] == 'text':
                source_type = events['source']['type']
                buffer_id = source_type
                if source_type == 'user':
                    buffer_id = buffer_id + events['source']['userId']
                elif source_type == 'group':
                    buffer_id = buffer_id + events['source']['groupId']
                elif source_type == 'room':
                    buffer_id = buffer_id + events['source']['roomId']
                db = MongoClient(MONGODB_URI)
                doc = db.heroku_lq333lwm.issuebot.find_one({'room_id': buffer_id})
                if doc == None:
                    doc = db.heroku_lq333lwm.issuebot.insert_one({'room_id': buffer_id, 'issue_buffer':''})
                issue_buffer =  doc['issue_buffer']
                issue = Issue(issue_buffer)

                text = events['message']['text']
                if is_title(text):
                    issue.set_title(text)
                    db.heroku_lq333lwm.issuebot.update({'room_id': buffer_id},{'$set':{'issue_buffer': issue.to_json_string()}})
                elif is_category(text):
                    issue.set_category(text)
                    db.heroku_lq333lwm.issuebot.update({'room_id': buffer_id},{'$set':{'issue_buffer': issue.to_json_string()}})
                elif is_trigger_summit(text):
                    if issue.is_empty():
                        pass
                    else:
                        airtable_headers = {
                            'authorization': 'Bearer ' + AIRTABLE_API_KEY,
                            'content-type': 'application/json'
                        }
                        r = requests.post(AIRTABEL_API_URL, data=issue.to_json_string(), headers=airtable_headers)
                        payload = {'replyToken':events['replyToken'], 'messages':[{ 'type': 'text', 'text': 'issue created: ' + AIRTABEL_SHARED_URL + json.loads(r.text)['id']}]}
                        requests.post(LINE_API_URL, headers=headers, data=json.dumps(payload))
                        db.heroku_lq333lwm.issuebot.update({'room_id': buffer_id},{'$set':{'issue_buffer': Issue().to_json_string()}})
                else:
                    issue.append_description(text)
                    db.heroku_lq333lwm.issuebot.update({'room_id': buffer_id},{'$set':{'issue_buffer': issue.to_json_string()}})
                    
            if events['message']['type'] == 'image':
                content_id = events['message']['id']
                db = MongoClient(MONGODB_URI)
                issue_buffer =  db.heroku_lq333lwm.issuebot.find_one({'room_id': buffer_id})['issue_buffer']
                issue = Issue(issue_buffer)                
                issue.append_attachment(HOST + 'line-content/{content_id}'.format(content_id=content_id))
                db.heroku_lq333lwm.issuebot.update({'room_id': buffer_id},{'$set':{'issue_buffer': issue.to_json_string()}})
    except:
        print('Unexpected error:', traceback.format_exc())
        sys.stdout.flush()
        return 'foo'
    sys.stdout.flush()
    return 'bar'

import io
from flask import send_file
@app.route('/line-content/<string:id>')
def proxy(id):
    headers = {'Authorization':'Bearer ' + LINE_CHANNEL_SECRET}
    c = requests.get(LINE_CONTENT_URL + '{content_id}/content'.format(content_id=id), headers=headers)
    return send_file(io.BytesIO(c.content), attachment_filename='{content_id}.jpeg'.format(content_id=id), mimetype='image/jpg')

if __name__ == '__main__':
    app.run(debug=False)
