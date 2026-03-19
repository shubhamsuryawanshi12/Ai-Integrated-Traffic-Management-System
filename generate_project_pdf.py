"""
Generate a comprehensive PDF document for the UrbanFlow project.
Contains all project information: architecture, tech stack, workflows, APIs, etc.
"""

from fpdf import FPDF
import os
from datetime import datetime


class UrbanFlowPDF(FPDF):
    """Custom PDF class with header/footer for UrbanFlow project."""

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, "UrbanFlow - AI-Powered Adaptive Traffic Management System", align="L")
            self.ln(4)
            self.set_draw_color(0, 150, 136)
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def chapter_title(self, title):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(0, 105, 92)
        self.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 150, 136)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(33, 33, 33)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def sub_section_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(66, 66, 66)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet_point(self, text, indent=15):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        x = self.get_x()
        self.cell(indent, 5.5, "")
        self.set_font("Helvetica", "B", 10)
        self.cell(4, 5.5, "-")
        self.set_font("Helvetica", "", 10)
        self.cell(3, 5.5, "")
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def code_block(self, text, width=190):
        self.set_font("Courier", "", 8)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(40, 40, 40)
        lines = text.strip().split("\n")
        for line in lines:
            safe = line.encode('latin-1', errors='replace').decode('latin-1')
            self.cell(width, 4.5, "  " + safe, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def add_table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)

        # Header
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(0, 150, 136)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        fill = False
        for row in rows:
            if fill:
                self.set_fill_color(245, 245, 245)
            else:
                self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                safe = str(cell).encode('latin-1', errors='replace').decode('latin-1')
                self.cell(col_widths[i], 6, safe, border=1, fill=True, align="C" if i > 0 else "L")
            self.ln()
            fill = not fill
        self.ln(4)

    def check_page_break(self, h=60):
        if self.get_y() + h > 270:
            self.add_page()


def create_pdf():
    pdf = UrbanFlowPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ===================== COVER PAGE =====================
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(0, 105, 92)
    pdf.cell(0, 20, "UrbanFlow", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "AI-Powered Adaptive Traffic Management System", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_draw_color(0, 150, 136)
    pdf.set_line_width(1)
    pdf.line(50, pdf.get_y(), 160, pdf.get_y())
    pdf.ln(15)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Comprehensive Project Documentation", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Version: 1.0", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 8, "Hackathon 2026", align="C", new_x="LMARGIN", new_y="NEXT")

    # ===================== TABLE OF CONTENTS =====================
    pdf.add_page()
    pdf.chapter_title("Table of Contents")
    toc_items = [
        "1. Executive Summary",
        "2. Project Overview",
        "3. System Architecture",
        "4. Technology Stack",
        "5. System Workflow",
        "6. Computer Vision Pipeline",
        "7. AI/ML Engine (Reinforcement Learning)",
        "8. API Documentation",
        "9. Frontend Dashboard",
        "10. Mobile Camera Server",
        "11. Configuration & Deployment",
        "12. Project File Structure",
        "13. Current System Status",
        "14. Advanced Features Roadmap",
        "15. Setup & Running Instructions",
    ]
    for item in toc_items:
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(33, 33, 33)
        pdf.cell(0, 8, item, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # ===================== 1. EXECUTIVE SUMMARY =====================
    pdf.add_page()
    pdf.chapter_title("1. Executive Summary")
    pdf.body_text(
        "UrbanFlow is an AI-powered adaptive traffic signal control system designed to reduce urban congestion "
        "by dynamically optimizing traffic light timings. Unlike traditional fixed-timer systems, UrbanFlow "
        "uses a combination of computer vision (for real-time vehicle detection), reinforcement learning "
        "(for intelligent signal optimization), and a real-time dashboard (for monitoring and control)."
    )
    pdf.body_text(
        "The system processes live camera feeds from mobile phones using OpenCV and YOLOv8 for vehicle detection "
        "and traffic signal recognition. An Actor-Critic (A2C) neural network, built with PyTorch, learns optimal "
        "signal phase timings by minimizing vehicle wait times and queue lengths. The React-based dashboard provides "
        "operators with a live traffic map, real-time statistics, analytics charts, an AI chatbot, and full simulation controls."
    )
    pdf.body_text(
        "Key innovation: UrbanFlow adapts signal timing based on actual traffic demand, potentially reducing average "
        "wait times by 30-40% compared to fixed-timer traffic lights. At 3 AM with no traffic, lights change quickly. "
        "During rush hour at 5 PM, green phases extend for congested directions."
    )

    # ===================== 2. PROJECT OVERVIEW =====================
    pdf.add_page()
    pdf.chapter_title("2. Project Overview")

    pdf.section_title("2.1 Problem Statement")
    pdf.body_text(
        "Urban traffic congestion is a growing global problem causing increased fuel consumption, air pollution, "
        "commuter stress, and economic losses. Traditional traffic signal systems use fixed timers that do not "
        "respond to real-time traffic conditions, leading to inefficient traffic flow."
    )

    pdf.section_title("2.2 Proposed Solution")
    pdf.body_text("UrbanFlow addresses this with four core capabilities:")
    pdf.bullet_point("SEES: Uses mobile phone cameras + OpenCV/YOLO to detect vehicles and traffic signal states in real-time.")
    pdf.bullet_point("THINKS: Uses an A2C Reinforcement Learning agent (PyTorch) to compute optimal signal phase timings.")
    pdf.bullet_point("ACTS: Optimizes traffic signal phases to minimize waiting time and queue length.")
    pdf.bullet_point("SHOWS: Provides a React-based real-time dashboard with maps, charts, analytics, and chatbot.")

    pdf.section_title("2.3 Key Features")
    pdf.bullet_point("Real-time vehicle detection via mobile camera (OpenCV + YOLOv8)")
    pdf.bullet_point("Traffic signal state recognition (HSV color detection + Hough Circle Transform)")
    pdf.bullet_point("AI-powered signal optimization using Actor-Critic Reinforcement Learning (A2C)")
    pdf.bullet_point("4-intersection traffic simulation with SUMO integration (mock mode available)")
    pdf.bullet_point("Live dashboard with interactive map (Leaflet), charts (Recharts), and real-time WebSocket updates")
    pdf.bullet_point("Firebase authentication (Google OAuth + Email/Password)")
    pdf.bullet_point("Mobile camera streaming from any phone on the same Wi-Fi network")
    pdf.bullet_point("AI Chatbot for traffic queries")
    pdf.bullet_point("Emergency siren trigger and green-impact CO2 tracking")
    pdf.bullet_point("Explainable AI panel showing decision reasoning")

    pdf.section_title("2.4 Operating Modes")
    pdf.add_table(
        ["Mode", "Description", "Use Case"],
        [
            ["Simulation", "SUMO/Mock generates traffic; AI optimizes signals", "Testing & Training the AI"],
            ["Real-World", "Phone camera detects real traffic; AI suggests timing", "Live deployment at intersection"],
            ["Hybrid", "Simulation (70%) + Camera (30%) combined", "Calibrating sim with real data"],
        ],
        [35, 90, 65]
    )

    # ===================== 3. SYSTEM ARCHITECTURE =====================
    pdf.add_page()
    pdf.chapter_title("3. System Architecture")

    pdf.section_title("3.1 High-Level Architecture")
    pdf.body_text(
        "The system consists of three independently running services that communicate via REST APIs and WebSockets:"
    )
    pdf.add_table(
        ["Service", "Port", "Technology", "Purpose"],
        [
            ["Backend API", "8000", "FastAPI + Socket.IO", "Traffic simulation + AI control"],
            ["Camera Server", "5000", "Flask + Socket.IO + OpenCV", "Real-time video processing"],
            ["Frontend", "3000", "React.js", "Dashboard visualization"],
        ],
        [40, 20, 65, 65]
    )

    pdf.section_title("3.2 Architecture Diagram")
    pdf.code_block(
        "Mobile Phone  --->  Camera Server (5000)  --->  React Dashboard (3000)\n"
        "(Camera Feed)  <---  Flask + SocketIO       |         |\n"
        "                                            |         |\n"
        "                    Simulation API (8000) <--+\n"
        "                    FastAPI + SocketIO\n"
        "                    + SUMO Environment\n"
        "                    + RL Agent (A2C)"
    )

    pdf.section_title("3.3 Communication Protocols")
    pdf.bullet_point("REST API (HTTP): Frontend <-> Backend for simulation control, status queries")
    pdf.bullet_point("WebSocket (Socket.IO): Real-time traffic updates broadcast from backend to dashboard")
    pdf.bullet_point("WebSocket (Socket.IO): Mobile camera frames sent to Camera Server for processing")

    pdf.section_title("3.4 Data Flow")
    pdf.body_text(
        "1. Phone captures video frame every ~200ms\n"
        "2. Frame is Base64-encoded and sent via Socket.IO to Camera Server (port 5000)\n"
        "3. Camera Server decodes frame and runs Vehicle Detector + Signal Detector\n"
        "4. Detection results are emitted back to the phone and stored in /api/latest\n"
        "5. Simulation Engine (port 8000) runs RL Agent to optimize signal phases\n"
        "6. Every 2 seconds, intersection states are broadcast via WebSocket to Dashboard\n"
        "7. Dashboard renders live map, charts, signal indicators, and activity log"
    )

    # ===================== 4. TECHNOLOGY STACK =====================
    pdf.add_page()
    pdf.chapter_title("4. Technology Stack")

    pdf.section_title("4.1 Frontend")
    pdf.add_table(
        ["Technology", "Version", "Purpose"],
        [
            ["React.js", "19.x", "UI framework (component-based SPA)"],
            ["React Router", "7.x", "Client-side routing"],
            ["Material-UI (MUI)", "7.x", "Pre-built UI components"],
            ["Tailwind CSS", "3.x", "Utility-first CSS styling"],
            ["Recharts", "3.x", "Data visualization charts"],
            ["React-Leaflet", "5.x", "Interactive traffic map"],
            ["Framer Motion", "12.x", "Animations and transitions"],
            ["Axios", "1.x", "HTTP client for API calls"],
            ["Socket.IO Client", "4.x", "Real-time WebSocket updates"],
            ["Firebase SDK", "12.x", "Authentication (Google/Email)"],
            ["React-CountUp", "6.x", "Animated number counters"],
        ],
        [50, 25, 115]
    )

    pdf.section_title("4.2 Backend")
    pdf.add_table(
        ["Technology", "Version", "Purpose"],
        [
            ["Python", "3.11+", "Primary backend language"],
            ["FastAPI", "0.109+", "REST API framework (async, auto-docs)"],
            ["Uvicorn", "0.27+", "ASGI server"],
            ["Pydantic", "2.x", "Data validation & serialization"],
            ["python-socketio", "5.x", "WebSocket server for real-time updates"],
            ["Flask", "3.x", "Camera server framework (port 5000)"],
            ["Flask-SocketIO", "5.x", "WebSocket support for camera"],
            ["Eventlet", "0.33+", "Async networking for Flask"],
            ["Firebase Admin", "6.x", "Server-side authentication"],
        ],
        [50, 25, 115]
    )

    pdf.check_page_break(80)
    pdf.section_title("4.3 AI/ML Engine")
    pdf.add_table(
        ["Technology", "Version", "Purpose"],
        [
            ["PyTorch", "2.x", "Deep learning framework (RL agent)"],
            ["NumPy", "Latest", "Numerical computing"],
            ["Pandas", "Latest", "Data processing"],
            ["Scikit-learn", "Latest", "Machine learning utilities"],
            ["OpenCV", "4.8+", "Computer vision (vehicle detection)"],
            ["Ultralytics (YOLOv8)", "8.x", "Object detection model"],
            ["Pillow", "10+", "Image processing"],
            ["imutils", "0.5+", "OpenCV convenience functions"],
        ],
        [55, 25, 110]
    )

    pdf.check_page_break(50)
    pdf.section_title("4.4 Simulation & DevOps")
    pdf.add_table(
        ["Technology", "Version", "Purpose"],
        [
            ["SUMO", "1.19+", "Traffic simulation engine"],
            ["TraCI", "Built-in", "SUMO Python API for control"],
            ["Docker", "24+", "Containerization"],
            ["Docker Compose", "2.x", "Multi-container orchestration"],
            ["Git / GitHub", "-", "Version control"],
        ],
        [50, 25, 115]
    )

    # ===================== 5. SYSTEM WORKFLOW =====================
    pdf.add_page()
    pdf.chapter_title("5. System Workflow")

    pdf.section_title("Phase 1: Data Collection (The Eyes)")
    pdf.body_text(
        "The user opens http://<PC-IP>:5000 on their mobile phone (same Wi-Fi). The browser requests camera access. "
        "Every ~200ms, a frame is captured from the phone camera, converted to Base64 JPEG, and sent via Socket.IO "
        "to the Camera Server."
    )

    pdf.section_title("Phase 2: Perception (Computer Vision)")
    pdf.body_text(
        "Each frame is processed through TWO parallel detectors:"
    )
    pdf.bullet_point("Vehicle Detector: Uses BackgroundSubtractorMOG2 (motion-based) or YOLOv8 to detect and count vehicles.")
    pdf.bullet_point("Signal Detector: Uses HSV color masking + Hough Circle Transform to detect traffic signal state (Red/Yellow/Green).")

    pdf.section_title("Phase 3: Lane Assignment & Metrics")
    pdf.body_text(
        "The camera frame is divided into 4 quadrants (North/South/East/West). Each detected vehicle is assigned to a "
        "lane based on its center point position. Per-lane metrics are computed: vehicle count, queue length, average speed."
    )

    pdf.section_title("Phase 4: AI Decision Making (The Brain)")
    pdf.body_text(
        "The RL Agent receives a 32-dimensional state vector (queue, vehicles, speed, phase for each of 4 intersections). "
        "The Actor-Critic neural network outputs action probabilities and a state value. An action is sampled: "
        "0=Green, 1=Yellow, 2=Red, 3=Extended Green. The reward is calculated as: reward = -(waiting_time + 10 x stopped_vehicles)."
    )

    pdf.section_title("Phase 5: Signal Control (The Action)")
    pdf.body_text(
        "The chosen action is applied to the intersection. In SUMO mode, this changes the actual simulation signal. "
        "In Mock mode, the phase is stored in memory and broadcast to the dashboard. In the future, it could control "
        "physical IoT traffic controllers."
    )

    pdf.section_title("Phase 6: Dashboard Visualization (The Display)")
    pdf.body_text(
        "The React dashboard at localhost:3000 receives WebSocket broadcasts every 2 seconds. It renders real-time "
        "signal indicators, vehicle counts, lane statistics, an interactive traffic map, vehicle count history chart, "
        "activity log, and CO2 impact tracking."
    )

    pdf.check_page_break(50)
    pdf.section_title("Complete Loop Timing")
    pdf.add_table(
        ["Time", "Event"],
        [
            ["t=0.0s", "Phone captures frame"],
            ["t=0.1s", "Socket.IO sends frame to server"],
            ["t=0.2s", "Server decodes frame (Base64 -> OpenCV)"],
            ["t=0.3s", "Vehicle + Signal detection complete"],
            ["t=0.4s", "Lane assignment + speed + queue calculated"],
            ["t=0.5s", "Results emitted back; /api/latest updated"],
            ["t=1.0s", "RL Agent reads state, picks action, applies to signal"],
            ["t=2.0s", "WebSocket broadcast to Dashboard; UI updates"],
        ],
        [25, 165]
    )

    # ===================== 6. COMPUTER VISION PIPELINE =====================
    pdf.add_page()
    pdf.chapter_title("6. Computer Vision Pipeline")

    pdf.section_title("6.1 Vehicle Detection")
    pdf.sub_section_title("Motion Detection (BackgroundSubtractorMOG2) - Fallback")
    pdf.body_text(
        "1. Background model learns the 'empty road' over 200 frames.\n"
        "2. New/moving pixels are detected via background subtraction.\n"
        "3. Morphology cleanup removes noise.\n"
        "4. Contours are found and filtered by area (>500px2) and aspect ratio (0.2-4.0).\n"
        "5. Each passing contour is counted as a vehicle."
    )
    pdf.add_table(
        ["Parameter", "Value", "Description"],
        [
            ["history", "200", "Background model memory (frames)"],
            ["varThreshold", "25", "Detection sensitivity"],
            ["detectShadows", "false", "Ignore shadow artifacts"],
            ["min_area", "500 px2", "Minimum contour area for vehicle"],
            ["max_area", "50% frame", "Max contour (full-frame noise filter)"],
            ["aspect_ratio", "0.2 - 4.0", "Vehicle shape filter"],
        ],
        [45, 35, 110]
    )

    pdf.sub_section_title("YOLOv8 (When Available)")
    pdf.add_table(
        ["Parameter", "Value", "Description"],
        [
            ["Model", "yolov8n.pt", "YOLOv8 Nano (6.5MB, fast)"],
            ["Confidence", "0.5", "Minimum detection confidence"],
            ["IOU Threshold", "0.45", "Non-max suppression overlap"],
            ["Image Size", "640px", "Input image size"],
        ],
        [45, 35, 110]
    )

    pdf.section_title("6.2 Traffic Signal Detection")
    pdf.body_text(
        "Uses HSV color space conversion + color masking to detect Red, Yellow, and Green traffic signals. "
        "Hough Circle Transform finds circular signal lights. The dominant color determines the signal state."
    )
    pdf.add_table(
        ["Color", "H Low", "H High", "S Low", "S High", "V Low", "V High"],
        [
            ["Red (range 1)", "0", "10", "100", "255", "100", "255"],
            ["Red (range 2)", "160", "180", "100", "255", "100", "255"],
            ["Yellow", "15", "35", "100", "255", "100", "255"],
            ["Green", "40", "90", "50", "255", "50", "255"],
        ],
        [35, 22, 22, 22, 22, 22, 22]
    )

    # ===================== 7. AI/ML ENGINE =====================
    pdf.add_page()
    pdf.chapter_title("7. AI/ML Engine (Reinforcement Learning)")

    pdf.section_title("7.1 Actor-Critic (A2C) Architecture")
    pdf.body_text(
        "The RL agent uses an Actor-Critic neural network with the following architecture:"
    )
    pdf.code_block(
        "Input Layer (32 neurons)  -->  Hidden Layer (128 neurons + ReLU)\n"
        "                                     |\n"
        "                            +--------+--------+\n"
        "                            |                 |\n"
        "                       ACTOR HEAD        CRITIC HEAD\n"
        "                       (4 outputs)       (1 output)\n"
        "                        Softmax           Value\n"
        "                            |                 |\n"
        "                     Action Probs      State Value\n"
        "                     [0.4,0.1,0.3,0.2]    -25.3"
    )

    pdf.section_title("7.2 State Vector (Input)")
    pdf.body_text(
        "32-dimensional vector: 4 features per intersection x 4 intersections = 16 core features + 16 padding zeros."
    )
    pdf.add_table(
        ["Feature", "Description", "Range"],
        [
            ["queue_length", "Number of stopped vehicles", "0 - 20"],
            ["vehicle_count", "Total vehicles at intersection", "5 - 50"],
            ["avg_speed", "Average vehicle speed (m/s)", "5 - 15"],
            ["phase", "Current signal phase", "0=Green, 1=Yellow, 2=Red"],
        ],
        [50, 95, 45]
    )

    pdf.section_title("7.3 Action Space")
    pdf.add_table(
        ["Action", "Signal Phase", "Meaning"],
        [
            ["0", "Green", "Normal green phase"],
            ["1", "Yellow", "Transition/caution phase"],
            ["2", "Red", "Stop phase"],
            ["3", "Extended Green", "Extended green for heavy traffic"],
        ],
        [30, 50, 110]
    )

    pdf.section_title("7.4 Reward Function")
    pdf.code_block("reward = -(total_waiting_time + 10 * total_stopped_vehicles)")
    pdf.body_text(
        "The agent learns to minimize both waiting time and queue length. Typical reward range: -100 to -10 per step. "
        "Over training: Episode 1: -95 (random) -> Episode 50: -45 -> Episode 100: -28 (optimized)."
    )

    pdf.section_title("7.5 Training Configuration")
    pdf.add_table(
        ["Parameter", "Value"],
        [
            ["Optimizer", "Adam (lr=0.001)"],
            ["Discount Factor (gamma)", "0.99"],
            ["Steps per Episode", "1000"],
            ["Target Episodes", "100+"],
            ["Framework", "PyTorch"],
        ],
        [80, 110]
    )

    # ===================== 8. API DOCUMENTATION =====================
    pdf.add_page()
    pdf.chapter_title("8. API Documentation")

    pdf.section_title("8.1 Simulation API (Port 8000)")
    pdf.sub_section_title("FastAPI Endpoints")
    pdf.add_table(
        ["Method", "Endpoint", "Description"],
        [
            ["GET", "/", "API root - returns status"],
            ["GET", "/health", "Health check"],
            ["POST", "/api/v1/simulation/start", "Start traffic simulation"],
            ["POST", "/api/v1/simulation/stop", "Stop traffic simulation"],
            ["GET", "/api/v1/simulation/status", "Get simulation status"],
            ["GET", "/api/v1/traffic/*", "Traffic data endpoints"],
            ["GET", "/api/v1/ml/*", "ML model endpoints"],
            ["POST", "/api/v1/chatbot/*", "AI chatbot endpoints"],
        ],
        [20, 80, 90]
    )

    pdf.sub_section_title("WebSocket Events (Port 8000)")
    pdf.add_table(
        ["Event", "Direction", "Description"],
        [
            ["connect", "Client -> Server", "Client connects to WebSocket"],
            ["traffic_update", "Server -> Client", "Intersection states broadcast (every 2s)"],
            ["disconnect", "Client -> Server", "Client disconnects"],
        ],
        [45, 50, 95]
    )

    pdf.check_page_break(80)
    pdf.section_title("8.2 Camera Server API (Port 5000)")
    pdf.add_table(
        ["Method", "Endpoint", "Description"],
        [
            ["GET", "/", "Camera HTML page (for mobile)"],
            ["GET", "/api/status", "Server status, frame count, FPS"],
            ["GET", "/api/latest", "Latest detection results"],
            ["GET", "/api/debug", "Debug info (CV status, detector stats)"],
            ["GET", "/api/rl_state", "RL state vector + reward"],
            ["POST", "/api/collect/start", "Start data collection"],
            ["POST", "/api/collect/stop", "Stop data collection"],
            ["GET", "/api/collect/export", "Export collected data as JSON"],
        ],
        [20, 65, 105]
    )

    pdf.sub_section_title("WebSocket Events (Port 5000)")
    pdf.add_table(
        ["Event", "Direction", "Data"],
        [
            ["frame", "Client -> Server", "{ image: '<base64 JPEG>' }"],
            ["detection_result", "Server -> Client", "Detection JSON (signal, vehicles, metrics)"],
            ["status", "Server -> Client", "{ connected: true }"],
        ],
        [45, 50, 95]
    )

    # ===================== 9. FRONTEND DASHBOARD =====================
    pdf.add_page()
    pdf.chapter_title("9. Frontend Dashboard")

    pdf.section_title("9.1 Pages & Routing")
    pdf.add_table(
        ["Route", "Component", "Description"],
        [
            ["/", "LandingPage", "Welcome page with 'Enter Dashboard' button"],
            ["/dashboard", "Dashboard", "Main traffic monitoring dashboard"],
            ["/analytics", "Analytics", "Historical traffic analytics"],
            ["/login", "Login/Signup", "Firebase authentication"],
        ],
        [40, 50, 100]
    )

    pdf.section_title("9.2 Dashboard Components")
    pdf.bullet_point("TrafficMap: Interactive Leaflet map showing intersections with color-coded signal indicators")
    pdf.bullet_point("RealTimeStats: Live counters for total intersections, active vehicles, avg wait time, CO2 saved")
    pdf.bullet_point("CameraFeed: Live traffic camera viewer (connects to port 5000 camera server)")
    pdf.bullet_point("SignalControl: Visual traffic signal indicators for each intersection")
    pdf.bullet_point("VehicleChart: Recharts-based line/bar chart for vehicle count history")
    pdf.bullet_point("ExplainabilityPanel: Shows AI decision reasoning and feature importance")
    pdf.bullet_point("Chatbot: AI-powered traffic assistant for queries")
    pdf.bullet_point("SirenButton: Emergency siren trigger")
    pdf.bullet_point("SimulationControl: Start/Stop simulation with mode selection")

    pdf.section_title("9.3 State Management")
    pdf.body_text(
        "Uses React Context API with TrafficContext and AuthContext. TrafficContext manages real-time intersection data "
        "via Socket.IO connection. AuthContext manages Firebase authentication state."
    )

    # ===================== 10. MOBILE CAMERA SERVER =====================
    pdf.add_page()
    pdf.chapter_title("10. Mobile Camera Server")

    pdf.body_text(
        "The mobile camera server is a separate Flask application running on port 5000. It serves a camera HTML page "
        "designed for mobile devices. When accessed on a phone (same Wi-Fi), users can start their phone camera and "
        "stream video frames to the server in real-time."
    )

    pdf.section_title("10.1 Features")
    pdf.bullet_point("Mobile-optimized camera interface with Start/Stop/Switch controls")
    pdf.bullet_point("Real-time FPS counter and frame counter")
    pdf.bullet_point("Connection status indicator")
    pdf.bullet_point("Detection results overlay (Signal state, Confidence, Vehicles, Queue, Speed)")
    pdf.bullet_point("Camera warmup phase (first 30 frames) for background model initialization")
    pdf.bullet_point("Works in mock mode when OpenCV is unavailable")

    pdf.section_title("10.2 Configuration")
    pdf.add_table(
        ["Parameter", "Value"],
        [
            ["Port", "5000"],
            ["Max Frame Size", "10 MB"],
            ["Ping Timeout", "60 seconds"],
            ["Async Mode", "eventlet (fallback: threading)"],
            ["Frame Rate", "~5 FPS (200ms interval)"],
            ["Warmup Frames", "30"],
            ["CORS", "All origins (*)"],
        ],
        [70, 120]
    )

    # ===================== 11. CONFIGURATION & DEPLOYMENT =====================
    pdf.add_page()
    pdf.chapter_title("11. Configuration & Deployment")

    pdf.section_title("11.1 Server Configuration")
    pdf.add_table(
        ["Parameter", "Value", "File"],
        [
            ["Backend Port", "8000", "app/main.py"],
            ["Camera Server Port", "5000", "mobile_camera_server.py"],
            ["Frontend Port", "3000", "package.json (proxy)"],
            ["CORS", "All origins (*)", "Both servers"],
        ],
        [55, 50, 85]
    )

    pdf.section_title("11.2 Simulation Configuration")
    pdf.add_table(
        ["Parameter", "Value"],
        [
            ["Intersections", "4 (INT_1 to INT_4)"],
            ["Grid Layout", "2x2 (150px spacing)"],
            ["Step Interval", "1.0 second"],
            ["Broadcast Interval", "2.0 seconds"],
            ["Simulation Weight", "0.7 (in hybrid mode)"],
            ["Real-World Weight", "0.3 (in hybrid mode)"],
        ],
        [70, 120]
    )

    pdf.section_title("11.3 Docker Deployment")
    pdf.body_text("The project includes docker-compose.yml for containerized deployment:")
    pdf.code_block(
        "docker-compose up --build\n"
        "\n"
        "Services:\n"
        "  backend:  Port 8000 (FastAPI + SUMO)\n"
        "  frontend: Port 3000 (React, depends on backend)"
    )

    # ===================== 12. FILE STRUCTURE =====================
    pdf.add_page()
    pdf.chapter_title("12. Project File Structure")
    pdf.code_block(
        "UrbanFlow/\n"
        "|-- backend/\n"
        "|   |-- app/\n"
        "|   |   |-- main.py                        # FastAPI entry point\n"
        "|   |   |-- api/routes/\n"
        "|   |   |   |-- simulation.py              # Simulation APIs\n"
        "|   |   |   |-- traffic.py                 # Traffic data APIs\n"
        "|   |   |   |-- ml_model.py                # ML model APIs\n"
        "|   |   |   |-- chatbot.py                 # AI chatbot API\n"
        "|   |   |-- core/\n"
        "|   |   |   |-- socket_manager.py          # WebSocket manager\n"
        "|   |   |-- services/\n"
        "|   |       |-- ai_engine/\n"
        "|   |       |   |-- rl_agent.py            # A2C RL Agent\n"
        "|   |       |-- mobile_camera/\n"
        "|   |       |   |-- mobile_camera_server.py  # Flask Camera Server\n"
        "|   |       |-- sumo/\n"
        "|   |       |   |-- environment.py         # SUMO simulation env\n"
        "|   |       |-- vision/\n"
        "|   |           |-- vehicle_detector.py    # Vehicle detection\n"
        "|   |           |-- signal_detector.py     # Signal detection\n"
        "|   |           |-- camera_stream.py       # Camera handler\n"
        "|   |           |-- data_processor.py      # Data processing\n"
        "|   |           |-- hybrid_environment.py  # Hybrid sim+real\n"
        "|   |-- requirements-windows.txt           # Python dependencies\n"
        "|   |-- yolov8n.pt                         # YOLO model (6.5MB)\n"
        "|   |-- Dockerfile\n"
        "|\n"
        "|-- frontend/\n"
        "|   |-- src/\n"
        "|   |   |-- App.jsx                        # Main app router\n"
        "|   |   |-- components/                    # UI components\n"
        "|   |   |   |-- Dashboard/                 # Dashboard widgets\n"
        "|   |   |   |-- LandingPage.jsx            # Welcome page\n"
        "|   |   |-- context/                       # React contexts\n"
        "|   |   |   |-- AuthContext.jsx\n"
        "|   |   |   |-- TrafficContext.jsx\n"
        "|   |   |-- services/                      # API + Firebase\n"
        "|   |   |-- pages/                         # Page components\n"
        "|   |-- package.json\n"
        "|   |-- tailwind.config.js\n"
        "|   |-- Dockerfile\n"
        "|\n"
        "|-- sumo_files/                            # SUMO network files\n"
        "|-- Traffic ML Model/                      # ML model files\n"
        "|-- docker-compose.yml                     # Container orchestration\n"
        "|-- README.md\n"
        "|-- README_START.md                        # Setup instructions"
    )

    # ===================== 13. CURRENT STATUS =====================
    pdf.add_page()
    pdf.chapter_title("13. Current System Status")

    pdf.add_table(
        ["Component", "Status", "Mode"],
        [
            ["Backend API (FastAPI)", "Running", "Fully operational"],
            ["Frontend (React)", "Running", "Connected to backend"],
            ["Camera Server (Flask)", "Running", "OpenCV + Mock fallback"],
            ["RL Agent", "Running", "A2C with PyTorch"],
            ["YOLO Model", "Available", "yolov8n.pt present (6.5MB)"],
            ["SUMO Simulation", "Mock Mode", "Random traffic data generated"],
            ["PyTorch", "Installed", "CPU-only mode"],
            ["Firebase Auth", "Configured", "Google + Email/Password"],
            ["WebSocket Updates", "Active", "2-second broadcast interval"],
        ],
        [55, 40, 95]
    )

    # ===================== 14. ADVANCED FEATURES =====================
    pdf.add_page()
    pdf.chapter_title("14. Advanced Features Roadmap")

    pdf.section_title("14.1 Priority Matrix")
    pdf.add_table(
        ["Priority", "Feature", "Impact", "Effort"],
        [
            ["P1 (High)", "Transformer-Based Prediction", "High", "Medium"],
            ["P1 (High)", "Explainable AI (XAI)", "High", "Medium"],
            ["P2 (Med)", "Edge AI (TensorRT on Jetson)", "High", "High"],
            ["P2 (Med)", "Federated Learning", "High", "High"],
            ["P2 (Med)", "Emergency Vehicle Preemption", "High", "Medium"],
            ["P3 (Low)", "Graph Neural Networks (GNN)", "High", "High"],
            ["P3 (Low)", "Digital Twin (Unity/Unreal)", "Medium", "Very High"],
            ["P3 (Low)", "Mobile Citizen Portal", "Medium", "Medium"],
            ["P4 (Future)", "Drone-Based Monitoring", "Medium", "High"],
            ["P4 (Future)", "V2X Integration (5G)", "Medium", "High"],
            ["P4 (Future)", "Quantum Optimization", "Future", "High"],
        ],
        [30, 70, 35, 35]  # Adjusted widths: 30+70+35+35 = 170
    )

    pdf.section_title("14.2 Planned Enhancements")
    pdf.bullet_point("Transformer-based traffic flow prediction (replace LSTM with multi-head attention)")
    pdf.bullet_point("Graph Neural Networks for inter-intersection dependency modeling")
    pdf.bullet_point("Imitation Learning from expert traffic controllers")
    pdf.bullet_point("Meta-Learning (MAML) for rapid adaptation to new intersections")
    pdf.bullet_point("IoT sensor fusion: Radar + LiDAR + Camera")
    pdf.bullet_point("Blockchain audit trails for AI decisions")
    pdf.bullet_point("AR navigation overlays for traffic operators")
    pdf.bullet_point("Voice control interface for hands-free operation")

    # ===================== 15. SETUP INSTRUCTIONS =====================
    pdf.add_page()
    pdf.chapter_title("15. Setup & Running Instructions")

    pdf.section_title("15.1 Prerequisites")
    pdf.bullet_point("Python 3.12+")
    pdf.bullet_point("Node.js v18+ and npm")
    pdf.bullet_point("PowerShell (Windows)")

    pdf.section_title("15.2 One-Time Setup")
    pdf.sub_section_title("Backend (Python Virtual Environment)")
    pdf.code_block(
        "cd backend\n"
        "python -m venv .venv\n"
        ".venv\\Scripts\\activate\n"
        "pip install -r requirements-windows.txt"
    )

    pdf.sub_section_title("Frontend (Node Modules)")
    pdf.code_block(
        "cd frontend\n"
        "npm install"
    )

    pdf.section_title("15.3 Starting the Project")

    pdf.sub_section_title("Terminal 1: Backend Server")
    pdf.code_block(
        "cd backend\n"
        ".venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    )
    pdf.body_text("Access: http://localhost:8000")

    pdf.sub_section_title("Terminal 2: Frontend Dashboard")
    pdf.code_block(
        "cd frontend\n"
        "npm start"
    )
    pdf.body_text("Access: http://localhost:3000")

    pdf.sub_section_title("Terminal 3: Mobile Camera Server (Optional)")
    pdf.code_block(
        "cd backend\n"
        ".venv\\Scripts\\python.exe app/services/mobile_camera/mobile_camera_server.py"
    )
    pdf.body_text("Access: http://localhost:5000 (open on phone, same Wi-Fi)")

    pdf.section_title("15.4 Usage")
    pdf.body_text(
        "1. Open http://localhost:3000 in your browser.\n"
        "2. Click 'Enter Dashboard'.\n"
        "3. Click 'START SIMULATION' to begin the traffic simulation.\n"
        "4. (Optional) Open http://localhost:5000 on your mobile phone to start camera streaming.\n"
        "5. The dashboard will show live traffic data, signal states, and AI-optimized phase timings."
    )

    # ===================== SAVE =====================
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "UrbanFlow_Project_Documentation.pdf")
    pdf.output(output_path)
    print(f"\nPDF generated successfully: {output_path}")
    print(f"Total pages: {pdf.page_no()}")
    return output_path


if __name__ == "__main__":
    create_pdf()
