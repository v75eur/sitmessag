from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os, secrets
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'RickRoss1994@')
ADMIN_DEVERROUILLE = os.environ.get('ADMIN_DEVERROUILLE', 'RickRoss1994')
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

def clean_expired():
    messages = load_messages()
    now = datetime.now()
    new_messages = [m for m in messages if datetime.fromisoformat(m['expire']) > now]
    if len(new_messages) != len(messages):
        save_messages(new_messages)
    return new_messages

@app.route('/')
def home():
    return "OK"

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

# ===== COMPTEURS DE VISITEURS =====
VISITEURS_FILE = "visiteurs.json"
TOTAL_VISITEURS_FILE = "total_visiteurs.json"

def init_visiteurs():
    if not os.path.exists(VISITEURS_FILE):
        with open(VISITEURS_FILE, 'w') as f:
            json.dump({}, f)

def init_total():
    if not os.path.exists(TOTAL_VISITEURS_FILE):
        with open(TOTAL_VISITEURS_FILE, 'w') as f:
            json.dump({"total": 0}, f)

def get_online_count():
    init_visiteurs()
    try:
        with open(VISITEURS_FILE, 'r') as f:
            data = json.load(f)
        now = datetime.now().timestamp()
        active = {ip: ts for ip, ts in data.items() if now - ts < 300}
        return len(active)
    except:
        return 0

def get_total_count():
    init_total()
    try:
        with open(TOTAL_VISITEURS_FILE, 'r') as f:
            data = json.load(f)
        return data.get("total", 0)
    except:
        return 0

@app.route('/api/visiteur', methods=['POST'])
def enregistrer_visiteur():
    data = request.json
    ip = data.get('ip', '')
    if not ip:
        return jsonify({"error": "IP manquante"}), 400
    
    init_visiteurs()
    with open(VISITEURS_FILE, 'r') as f:
        visiteurs = json.load(f)
    now = datetime.now().timestamp()
    visiteurs[ip] = now
    with open(VISITEURS_FILE, 'w') as f:
        json.dump(visiteurs, f)
    
    init_total()
    with open(TOTAL_VISITEURS_FILE, 'r') as f:
        total_data = json.load(f)
    
    HISTORIQUE_IPS = "historique_ips.txt"
    is_new = False
    if not os.path.exists(HISTORIQUE_IPS):
        is_new = True
    else:
        with open(HISTORIQUE_IPS, 'r') as f:
            ips = f.read().splitlines()
            if ip not in ips:
                is_new = True
    
    if is_new:
        total_data["total"] = total_data.get("total", 0) + 1
        with open(TOTAL_VISITEURS_FILE, 'w') as f:
            json.dump(total_data, f)
        with open(HISTORIQUE_IPS, 'a') as f:
            f.write(ip + "\n")
    
    online = get_online_count()
    total = get_total_count()
    
    return jsonify({
        "status": "ok",
        "online": online,
        "total": total
    })

@app.route('/api/stats/visiteurs', methods=['GET'])
def stats_visiteurs():
    online = get_online_count()
    total = get_total_count()
    return jsonify({"online": online, "total": total})
