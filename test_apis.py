import urllib.request
import json

def test_get(url):
    try:
        req = urllib.request.urlopen(url)
        return req.getcode(), json.loads(req.read().decode())
    except urllib.error.HTTPError as e:
        try:
             res = json.loads(e.read().decode())
             return e.code, res
        except:
             return e.code, e.reason
    except Exception as e:
        return 500, str(e)

def test_post(url, data=None):
    try:
        req = urllib.request.Request(url, method='POST')
        if data is not None:
            req.add_header('Content-Type', 'application/json')
            data = json.dumps(data).encode()
        else:
            req.add_header('Content-Length', '0')
        res = urllib.request.urlopen(req)
        return res.getcode(), json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        try:
             res = json.loads(e.read().decode())
             return e.code, res
        except:
             return e.code, e.reason
    except Exception as e:
        return 500, str(e)

with open('api_test_results.txt', 'w') as f:
    f.write('--- Simulation API ---\n')
    f.write(f'Start: {test_post("http://127.0.0.1:8000/api/v1/simulation/start?mode=simulation")}\n')
    f.write(f'Status: {test_get("http://127.0.0.1:8000/api/v1/simulation/status")}\n')
    f.write(f'Weather Rain: {test_post("http://127.0.0.1:8000/api/v1/simulation/weather", {"mode": "rain"})}\n')
    f.write(f'Weather Fog: {test_post("http://127.0.0.1:8000/api/v1/simulation/weather", {"mode": "fog"})}\n')
    f.write(f'Weather Clear: {test_post("http://127.0.0.1:8000/api/v1/simulation/weather", {"mode": "clear"})}\n')
    f.write(f'Emergency: {test_post("http://127.0.0.1:8000/api/v1/simulation/emergency?intersection_id=INT_1&active=true")}\n')

    f.write('\n--- Parking API ---\n')
    zones = test_get("http://127.0.0.1:8000/api/v1/parking/zones")
    if type(zones[1]) == list:
         f.write(f'Zones count: {len(zones[1])}\n')
         f.write(f'Zone[0] keys: {list(zones[1][0].keys())}\n')
         f.write(f'Zone[0] lat, lng: {zones[1][0].get("lat")}, {zones[1][0].get("lng")}\n')
    else:
         f.write(f'Zones: {zones}\n')
    
    f.write(f'Predict PZ_001: {test_get("http://127.0.0.1:8000/api/v1/parking/predict/PZ_001")}\n')
    f.write(f'Predict INVALID: {test_get("http://127.0.0.1:8000/api/v1/parking/predict/INVALID")}\n')

    f.write('\n--- Prediction API ---\n')
    res = test_get("http://127.0.0.1:8000/api/v1/prediction/forecast")
    count = len(res[1]['forecast']) if type(res[1]) == dict and 'forecast' in res[1] else res[1]
    f.write(f'Forecast items count: {count}\n')
    if type(res[1]) == dict and 'forecast' in res[1] and len(res[1]['forecast']) > 0:
        f.write(f'Forecast[0] keys: {list(res[1]["forecast"][0].keys())}\n')

    f.write('\n--- Routing API ---\n')
    f.write(f'Optimize body missing field: {test_post("http://127.0.0.1:8000/api/v1/routing/optimize", {})}\n')
    f.write(f'Optimize: {test_post("http://127.0.0.1:8000/api/v1/routing/optimize", {"origin": "17.6868, 75.9060", "destination": "17.6599, 75.9064"})}\n')

    f.write('\n--- Chatbot API ---\n')
    f.write(f'Chat empty body: {test_post("http://127.0.0.1:8000/api/v1/chatbot/chat", {})}\n')
    f.write(f'Chat: {test_post("http://127.0.0.1:8000/api/v1/chatbot/chat", {"message": "What is the current traffic on Vijapur Road?"})}\n')

    f.write('\n--- Camera Server API ---\n')
    f.write(f'Status: {test_get("http://127.0.0.1:5000/api/status")}\n')
    f.write(f'Latest: {test_get("http://127.0.0.1:5000/api/latest")}\n')
    f.write(f'RL State: {test_get("http://127.0.0.1:5000/api/rl_state")}\n')

    f.write('\n--- Stopping Simulation ---\n')
    f.write(f'Stop: {test_post("http://127.0.0.1:8000/api/v1/simulation/stop")}\n')
    f.write(f'Status after stop: {test_get("http://127.0.0.1:8000/api/v1/simulation/status")}\n')
