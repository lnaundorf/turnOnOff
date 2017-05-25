from flask import Flask, render_template, jsonify, redirect, request, url_for, make_response
import requests
import json
import os.path
from paramiko.client import SSHClient, AutoAddPolicy
from decorators import password_protect

CHECK_TIMEOUT_SECONDS = 1.0

app = Flask(__name__)
app.debug = True

PIMATIC_CONFIG = None
SERVERS = {}
PASSWORD = None

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, "settings.json")) as settings_file:
    settings = json.load(settings_file)
    PIMATIC = settings['pimatic']
    PASSWORD = settings.get('password')
    
    for server in settings['servers']:
        SERVERS[server['pimatic_id']] = server


class Status:
    OFFLINE = 0
    TURNED_ON = 1
    ONLINE = 2
    TURNED_OFF = 3


@app.route('/status')
@password_protect(PASSWORD)
def check_status():
    for server in SERVERS.values():
        check_online(server)
        
    server_list = [server for server in SERVERS.values()]

    return jsonify(server_list)


def set_server_state(server, state):
    server['state'] = state
    if state in (Status.OFFLINE, Status.ONLINE):
        server['last_clean_state'] = state
        
    return state


def server_not_found():
    return jsonify({
        "success": False,
        "error": "Server not found"
    }), 404


def check_online(server):
    # First check pimatic state
    pimatic_url = '%s/api/variables/%s.state' % (PIMATIC['host'], server['pimatic_id'])
    response = requests.get(pimatic_url, auth=(PIMATIC['username'], PIMATIC['password']))
    
    json_response = response.json()

    state = json_response['variable']['value']
    
    if state == 0:
        return set_server_state(server, Status.OFFLINE)
        
    # Switch is on, check url
    try:
        response = requests.get(server['check_address'], timeout=CHECK_TIMEOUT_SECONDS)
        print("Request: %s, Taken: %s ms" % (server['check_address'], str(response.elapsed.microseconds / 1000)))
        return set_server_state(server, Status.ONLINE)
    except Exception as e:
        print(e)
        if server.get('last_clean_state', None) == Status.ONLINE:
            return set_server_state(server, Status.TURNED_OFF)
        else:
            return set_server_state(server, Status.TURNED_ON)


@app.route('/server/<id>/turnOn')
@password_protect(PASSWORD)
def turn_on(id):
    server = SERVERS.get(id)
    if not server:
        return server_not_found()
        
    pimatic_url = '%s/api/device/%s/turnOn' % (PIMATIC['host'], server['pimatic_id'])
    response = requests.get(pimatic_url, auth=(PIMATIC['username'], PIMATIC['password']))
    
    return response.text


@app.route('/server/<id>/turnOff')
@password_protect(PASSWORD)
def turn_off(id):
    server = SERVERS.get(id)
    
    if not server:
        return server_not_found()

    exit_status = -1

    ssh_settings = server['ssh']
    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(ssh_settings['address'], username=ssh_settings['username'], password=ssh_settings['password'])
    stdin, stdout, stderr = client.exec_command('shutdown -p now')

    #print("stdout: " + str(stdout.readlines()))
    #print("stderr: " + str(stderr.readlines()))

    exit_status = stdout.channel.recv_exit_status()
    print("Shutdown, exit status: %s" % exit_status)

    client.close()
    
    return jsonify({
        "success": exit_status == 0
    })
    

@app.route('/login', methods = ['GET'])
def login_get():
    return render_template("login.html")


@app.route('/login', methods=['POST'])
def login_post():
    submitted_password = request.form.get('password')
    print("Submitted password: %s" % submitted_password)
    if submitted_password == PASSWORD:
        # Password correct
        resp = make_response(redirect(url_for('index')))
        resp.set_cookie('password', submitted_password)
        return resp
    else:
        return render_template("login.html", error_message="Falsches Passwort")


@app.route('/')
@password_protect(PASSWORD)
def index():
    print(json.dumps(SERVERS))
    return render_template('index.html')
    
if __name__ == "__main__":
    app.run(host="0.0.0.0")