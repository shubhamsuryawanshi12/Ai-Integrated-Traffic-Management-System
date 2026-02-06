import os
import subprocess

def generate_network():
    # Check if we are in the right directory or adjust paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    networks_dir = os.path.join(base_dir, "sumo_files", "networks")
    routes_dir = os.path.join(base_dir, "sumo_files", "routes")
    
    os.makedirs(networks_dir, exist_ok=True)
    os.makedirs(routes_dir, exist_ok=True)

    net_file = os.path.join(networks_dir, "simple_grid.net.xml")
    rou_file = os.path.join(routes_dir, "traffic_routes.rou.xml")

    # Command to generate 4x4 grid
    # netgenerate --grid --grid.number=4 --output-file=...
    print(f"Generating network file at {net_file}...")
    try:
        subprocess.run(["netgenerate", "--grid", "--grid.number=4", "--output-file", net_file], check=True)
        print("Network generated successfully.")
    except FileNotFoundError:
        print("Error: 'netgenerate' command not found. Ensure SUMO is installed and in PATH.")
        print("If running in Docker, exec into the container first.")
        # Create a dummy file if not found, to prevent crash? No, better to fail.
        return

    # Basic route file generation (random trips)
    # randomTrips.py -n simple_grid.net.xml -r traffic_routes.rou.xml -e 3600
    print(f"Generating route file at {rou_file}...")
    try:
        # randomTrips.py is usually in SUMO_HOME/tools
        # We can try to call it as a script if it's in path or via python -m
        # For simplicity, we'll try 'randomTrips.py' executable if available or assume standard path
        subprocess.run(["randomTrips.py", "-n", net_file, "-r", rou_file, "-e", "3600"], check=True)
        print("Routes generated successfully.")
    except Exception as e:
        print(f"Error generating routes: {e}")
        print("You may need to run this manually or ensure randomTrips.py is in PATH.")

if __name__ == "__main__":
    generate_network()
