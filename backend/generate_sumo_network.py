import os
import sys
import subprocess

def generate_network():
    # Check if we are in the right directory or adjust paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # D:\Hackathon
    
    networks_dir = os.path.join(base_dir, "sumo_files", "networks")
    routes_dir = os.path.join(base_dir, "sumo_files", "routes")
    
    os.makedirs(networks_dir, exist_ok=True)
    os.makedirs(routes_dir, exist_ok=True)

    net_file = os.path.join(networks_dir, "simple_grid.net.xml")
    rou_file = os.path.join(routes_dir, "traffic_routes.rou.xml")

    # 1. Generate Network (netgenerate)
    # ------------------------------------------------------------------
    print(f"Generating network file at {net_file}...")
    try:
        # Check standard installation path if not in PATH
        netgenerate_cmd = "netgenerate"
        if os.path.exists(r"D:\Software\bin\netgenerate.exe"):
             netgenerate_cmd = r"D:\Software\bin\netgenerate.exe"
             
        # Generate 4x4 grid
        subprocess.run([netgenerate_cmd, "--grid", "--grid.number=4", "--output-file", net_file], check=True)
        print(f"✅ Network created: {net_file}")
    except Exception as e:
        print(f"❌ Error generating network: {e}")
        # If network gen fails, we can't do routes.
        return

    # 2. Generate Routes (randomTrips.py)
    # ------------------------------------------------------------------
    print(f"Generating route file at {rou_file}...")
    try:
        sumo_home = os.environ.get("SUMO_HOME", r"D:\Software")
        random_trips_script = os.path.join(sumo_home, "tools", "randomTrips.py")
        
        if not os.path.exists(random_trips_script):
             print(f"⚠️ randomTrips.py not found at {random_trips_script}")
             print("   Please check your SUMO installation or SUMO_HOME variable.")
             return

        # Use sys.executable to run the python script
        # -e 3600 (1 hour duration)
        # -p 0.5 (period: 1 vehicle every 2 seconds roughly? No, period is inverse rate?)
        # -p 1.0 means 1 per second? verify flags. Default is fine usually.
        
        subprocess.run([sys.executable, random_trips_script, "-n", net_file, "-r", rou_file, "-e", "3600"], check=True)
        print(f"✅ Routes created: {rou_file}")
    except Exception as e:
        print(f"❌ Error generating routes: {e}")
        print("   You may need to run this manually.")

if __name__ == "__main__":
    generate_network()
