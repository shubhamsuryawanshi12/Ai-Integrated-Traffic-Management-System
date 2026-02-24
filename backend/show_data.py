import urllib.request, json

print("=" * 60)
print("  URBANFLOW SYSTEM - LIVE DATA SNAPSHOT")
print("=" * 60)

# 1. Camera Server Debug
debug = json.load(urllib.request.urlopen("http://localhost:5000/api/debug"))
print()
print("[CAMERA SERVER - Port 5000]")
print("  CV Available:     " + str(debug.get("cv_available")))
print("  Frames Processed: " + str(debug.get("frame_count")))
print("  Total Vehicles:   " + str(debug.get("total_vehicles")))
print("  Signal State:     " + str(debug.get("signal_state")))
print("  Lanes:            " + str(debug.get("lane_keys")))

# 2. Simulation Status
sim = json.load(urllib.request.urlopen("http://localhost:8000/api/v1/simulation/status"))
print()
print("[SIMULATION ENGINE - Port 8000]")
print("  Running: " + str(sim.get("running")))

# 3. RL State
rl = json.load(urllib.request.urlopen("http://localhost:5000/api/rl_state"))
print()
print("[RL AGENT STATE]")
print("  Reward:    " + str(rl.get("reward")))
state = rl.get("state", [])
print("  State Dim: " + str(len(state)) + " features")
if len(state) >= 16:
    labels = ["INT_1", "INT_2", "INT_3", "INT_4"]
    for i, label in enumerate(labels):
        offset = i * 4
        q = round(state[offset], 1)
        v = round(state[offset + 1], 1)
        s = round(state[offset + 2], 1)
        p = int(state[offset + 3])
        phase_name = ["GREEN", "YELLOW", "RED"][p] if p < 3 else str(p)
        print("  " + label + ": queue=" + str(q) + " vehicles=" + str(v) + " speed=" + str(s) + " phase=" + phase_name)

# 4. Latest camera detection
latest = json.load(urllib.request.urlopen("http://localhost:5000/api/latest"))
print()
print("[LATEST CAMERA DETECTION]")
if latest:
    print("  " + json.dumps(latest, indent=4)[:500])
else:
    print("  No phone connected yet (empty)")

print()
print("=" * 60)
