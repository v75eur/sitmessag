from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os, secrets
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'RickRoss1994@')
MESSAGES_FILE = 'messages.json'

def load_messages():
    try:
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_messages(messages):
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f, indent=2)

# Nettoyer les messages expirés (> 12 jours)
def clean_expired():
    messages = load_messages()
    now = datetime.now()
    new_messages = [m for m in messages if datetime.fromisoformat(m['expire']) > now]
    if len(new_messages) != len(messages):
        save_messages(new_messages)
    return new_messages

@app.route('/api/send', methods=['POST'])
def send():
    data = request.json
    required = ['nom', 'pays', 'ville', 'whatsapp', 'email', 'message']
    for field in required:
        if not data.get(field):
            return jsonify({'status': 'error', 'error': f'Champ {field} manquant'}), 400

    messages = load_messages()
    msg = {
        'id': secrets.token_urlsafe(12),
        'date': datetime.now().isoformat(),
        'expire': (datetime.now() + timedelta(days=12)).isoformat(),
        'service': data.get('service', 'Non spécifié'),
        'nom': data['nom'],
        'pays': data['pays'],
        'ville': data['ville'],
        'whatsapp': data['whatsapp'],
        'email': data['email'],
        'reseau': data.get('reseau', ''),
        'message': data['message'],
        'vu': False
    }
    messages.append(msg)
    save_messages(messages)
    return jsonify({'status': 'ok', 'id': msg['id']})

@app.route('/api/messages', methods=['POST'])
def get_messages():
    data = request.json
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({'status': 'error', 'error': 'Mot de passe incorrect'}), 403
    messages = clean_expired()
    return jsonify({'status': 'ok', 'messages': messages})

@app.route('/api/delete', methods=['POST'])
def delete():
    data = request.json
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({'status': 'error', 'error': 'Mot de passe incorrect'}), 403
    messages = load_messages()
    messages = [m for m in messages if m['id'] != data.get('id')]
    save_messages(messages)
    return jsonify({'status': 'ok'})

@app.route('/api/read', methods=['POST'])
def read():
    data = request.json
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({'status': 'error', 'error': 'Mot de passe incorrect'}), 403
    messages = load_messages()
    for m in messages:
        if m['id'] == data.get('id'):
            m['vu'] = True
            break
    save_messages(messages)
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, threaded=True)
