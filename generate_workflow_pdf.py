"""
UrbanFlow - Complete Project Workflow Documentation PDF
Covers: How to start, execution flow, page-by-page features, backend APIs.
"""
import os
from fpdf import FPDF
from datetime import datetime


class WorkflowPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, "UrbanFlow - Complete Project Workflow Documentation", align="L")
            self.ln(4)
            self.set_draw_color(59, 130, 246)
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def chapter_title(self, title):
        self.check_page_break(20)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(15, 23, 42)
        self.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(59, 130, 246)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def section_title(self, title):
        self.check_page_break(15)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 41, 59)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def sub_section(self, title):
        self.check_page_break(12)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(51, 65, 85)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(71, 85, 105)
        safe = text.encode('latin-1', errors='replace').decode('latin-1')
        self.multi_cell(0, 5.5, safe)
        self.ln(2)

    def bullet(self, text, indent=10):
        self.check_page_break(8)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(71, 85, 105)
        x = self.get_x()
        self.set_x(x + indent)
        self.cell(5, 5.5, "-")
        safe = text.encode('latin-1', errors='replace').decode('latin-1')
        self.multi_cell(0, 5.5, safe)
        self.ln(1)

    def code(self, text, width=190):
        self.check_page_break(len(text.strip().split("\n")) * 5 + 10)
        self.set_font("Courier", "", 9)
        self.set_fill_color(241, 245, 249)
        self.set_text_color(15, 23, 42)
        for line in text.strip().split("\n"):
            safe = line.encode('latin-1', errors='replace').decode('latin-1')
            self.cell(width, 5, "  " + safe, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)
        self.check_page_break(len(rows) * 8 + 15)
        self.set_font("Helvetica", "B", 10)
        self.set_fill_color(59, 130, 246)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, border=1, fill=True, align="C")
        self.ln()
        self.set_font("Helvetica", "", 9)
        self.set_text_color(51, 65, 85)
        fill = False
        for row in rows:
            self.set_fill_color(248, 250, 252) if fill else self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                safe = str(cell).encode('latin-1', errors='replace').decode('latin-1')
                self.cell(col_widths[i], 8, safe, border=1, fill=True, align="L")
            self.ln()
            fill = not fill
        self.ln(5)

    def check_page_break(self, h=60):
        if self.get_y() + h > 270:
            self.add_page()


def create_pdf():
    pdf = WorkflowPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ==================== TITLE PAGE ====================
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 38)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 20, "UrbanFlow", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 10, "AI-Powered Adaptive Traffic Management System", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_draw_color(59, 130, 246)
    pdf.set_line_width(1.5)
    pdf.line(50, pdf.get_y(), 160, pdf.get_y())
    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(0, 10, "Complete Project Workflow Documentation", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "SAMVED-2026 Hackathon | MIT Academy of Engineering", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Target: Solapur Municipal Corporation", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", align="C", new_x="LMARGIN", new_y="NEXT")

    # ==================== TABLE OF CONTENTS ====================
    pdf.add_page()
    pdf.chapter_title("Table of Contents")
    toc = [
        "1.  Project Overview",
        "2.  How to Start the Project (Step-by-Step)",
        "3.  Technology Stack",
        "4.  Project Folder Structure",
        "5.  System Architecture & Services",
        "6.  Application Execution Flow",
        "7.  Page-by-Page Feature Guide",
        "     7.1  Home Portal (Role Selection)",
        "     7.2  Traffic Police / Admin Dashboard",
        "     7.3  Enforcement Dashboard",
        "     7.4  Smart Parking Page",
        "     7.5  Analytics & Predictions Page",
        "     7.6  Citizen Mobile PWA",
        "     7.7  Mobile Camera Server",
        "8.  Backend API Endpoints",
        "9.  AI/ML Models Used",
        "10. Data Structures (In-Memory Database)",
        "11. Key Features Summary",
        "12. Future Enhancements",
        "13. Conclusion",
    ]
    for item in toc:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, item, new_x="LMARGIN", new_y="NEXT")

    # ==================== 1. OVERVIEW ====================
    pdf.add_page()
    pdf.chapter_title("1. Project Overview")

    pdf.section_title("What is UrbanFlow?")
    pdf.body(
        "UrbanFlow is an AI-powered Smart City Traffic Operating System. It replaces static, "
        "fixed-timer traffic signals with intelligent signals that adapt in real-time based on "
        "actual congestion, detected by phone cameras and simulated traffic data."
    )

    pdf.section_title("Problem Statement")
    pdf.bullet("Fixed traffic lights waste time - green for empty roads at 3 AM, red for jammed roads at rush hour.")
    pdf.bullet("No automated detection of hawkers blocking roads or illegally parked vehicles.")
    pdf.bullet("Citizens have no real-time visibility into parking availability or traffic congestion.")
    pdf.bullet("Traffic police, enforcement, and citizens all use separate, disconnected systems.")

    pdf.section_title("Our Solution")
    pdf.body(
        "UrbanFlow provides a unified platform with 4 role-based dashboards serving different city "
        "stakeholders. It uses Reinforcement Learning (A3C) to optimize signals, Computer Vision "
        "(YOLOv8) to detect violations, and predictive AI (Prophet/XGBoost) to forecast traffic."
    )

    pdf.section_title("Target Users")
    pdf.table(
        ["Role", "What They See", "Key Actions"],
        [
            ["Traffic Police", "Live traffic map, signal controls", "Monitor intersections, trigger emergency"],
            ["Enforcement Dept", "Hawker & parking violation alerts", "Respond to automated incident reports"],
            ["City Admin", "Full dashboard with all analytics", "Review AI decisions, weather controls"],
            ["Local Citizen", "Mobile-friendly parking & transit", "Find parking, report issues"],
        ],
        [35, 70, 85]
    )

    # ==================== 2. HOW TO START ====================
    pdf.add_page()
    pdf.chapter_title("2. How to Start the Project (Step-by-Step)")

    pdf.section_title("Prerequisites")
    pdf.bullet("Python 3.11 or higher installed")
    pdf.bullet("Node.js v18+ and npm installed")
    pdf.bullet("Git installed")
    pdf.bullet("Windows PowerShell (or any terminal)")

    pdf.section_title("Step 1: Clone the Repository")
    pdf.code("git clone https://github.com/shubhamsuryawanshi12/trafficmanagement.git\ncd Hackathon")

    pdf.section_title("Step 2: Set Up the Backend (Python Virtual Environment)")
    pdf.code(
        "cd backend\n"
        "python -m venv .venv\n"
        ".venv\\Scripts\\activate          # On Windows\n"
        "pip install -r requirements-windows.txt"
    )

    pdf.section_title("Step 3: Start the Backend Server (Terminal 1)")
    pdf.code(".venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    pdf.body("This starts the FastAPI server at http://localhost:8000. It handles the simulation engine, "
             "RL agent, parking APIs, prediction, routing, chatbot, and WebSocket broadcasts.")

    pdf.section_title("Step 4: Start the Frontend Dashboard (Terminal 2)")
    pdf.code("cd frontend\nnpm install      # First time only\nnpm start")
    pdf.body("This starts the React dashboard at http://localhost:3000. "
             "Open this URL in your browser to access the system.")

    pdf.section_title("Step 5: Start the Mobile Camera Server (Terminal 3 - Optional)")
    pdf.code("cd backend\n.venv\\Scripts\\python.exe app/services/mobile_camera/mobile_camera_server.py")
    pdf.body("This starts the Flask camera server at http://localhost:5000. "
             "Open this URL on your mobile phone (same Wi-Fi) to stream live camera feed for detection.")

    pdf.section_title("Step 6: Use the Application")
    pdf.bullet("Open http://localhost:3000 in your browser.")
    pdf.bullet("Select your role (Traffic Police / Enforcement / Admin / Citizen).")
    pdf.bullet("Click 'Enter Dashboard' to proceed to your role-specific view.")
    pdf.bullet("Click 'START SIMULATION' on the Dashboard page to begin the AI traffic loop.")
    pdf.bullet("(Optional) Open http://localhost:5000 on your phone for live camera streaming.")

    # ==================== 3. TECH STACK ====================
    pdf.add_page()
    pdf.chapter_title("3. Technology Stack")

    pdf.section_title("Frontend Technologies")
    pdf.table(
        ["Technology", "Purpose"],
        [
            ["React.js 19", "Component-based UI framework"],
            ["React Router 7", "Client-side page navigation"],
            ["Material-UI (MUI) 7", "Pre-built UI components (buttons, selects, cards)"],
            ["Tailwind CSS 3", "Utility-first CSS styling"],
            ["Recharts 3", "Data visualization (line charts, area charts, bar charts)"],
            ["React-Leaflet 5", "Interactive maps with markers"],
            ["Framer Motion 12", "Smooth animations and transitions"],
            ["Socket.IO Client 4", "Real-time WebSocket connection to backend"],
            ["Axios 1", "HTTP client for REST API calls"],
            ["Firebase SDK 12", "Authentication (Google OAuth)"],
        ],
        [55, 135]
    )

    pdf.section_title("Backend Technologies")
    pdf.table(
        ["Technology", "Purpose"],
        [
            ["Python 3.11+", "Primary backend language"],
            ["FastAPI", "REST API framework (Port 8000)"],
            ["python-socketio", "WebSocket server for real-time traffic broadcasts"],
            ["Flask", "Camera processing server (Port 5000)"],
            ["OpenCV 4.8+", "Computer vision for vehicle/signal/hawker detection"],
            ["YOLOv8 (Ultralytics)", "Deep learning object detection"],
            ["PyTorch 2", "Reinforcement Learning neural networks (A3C agent)"],
            ["Scikit-learn", "Anomaly detection (Isolation Forest)"],
            ["NetworkX", "Graph-based route optimization (Dijkstra)"],
        ],
        [55, 135]
    )

    # ==================== 4. FOLDER STRUCTURE ====================
    pdf.add_page()
    pdf.chapter_title("4. Project Folder Structure")

    pdf.code(
        "UrbanFlow/\n"
        "|\n"
        "|-- backend/\n"
        "|   |-- app/\n"
        "|   |   |-- main.py                    <-- BACKEND ENTRY POINT (FastAPI)\n"
        "|   |   |-- api/routes/\n"
        "|   |   |   |-- simulation.py          <-- Traffic simulation + RL agent\n"
        "|   |   |   |-- parking.py             <-- Smart parking zones API\n"
        "|   |   |   |-- prediction.py          <-- Traffic flow prediction API\n"
        "|   |   |   |-- routing.py             <-- Route optimization API\n"
        "|   |   |   |-- traffic.py             <-- Traffic data endpoints\n"
        "|   |   |   |-- ml_model.py            <-- ML model control endpoints\n"
        "|   |   |   |-- chatbot.py             <-- AI chatbot endpoint\n"
        "|   |   |-- core/\n"
        "|   |   |   |-- socket_manager.py      <-- WebSocket event broadcaster\n"
        "|   |   |-- services/\n"
        "|   |       |-- ai_engine/\n"
        "|   |       |   |-- a3c_agent.py        <-- Multi-Agent A3C RL Brain\n"
        "|   |       |   |-- traffic_predictor.py<-- Prophet+LSTM forecaster\n"
        "|   |       |   |-- anomaly_detector.py <-- IsolationForest detector\n"
        "|   |       |   |-- explainable_ai.py   <-- XAI reasoning module\n"
        "|   |       |-- mobile_camera/\n"
        "|   |       |   |-- mobile_camera_server.py <-- Flask Camera (Port 5000)\n"
        "|   |       |-- parking/\n"
        "|   |       |   |-- parking_manager.py  <-- Zone data + occupancy\n"
        "|   |       |   |-- occupancy_predictor.py <-- XGBoost prediction\n"
        "|   |       |-- routing/\n"
        "|   |       |   |-- route_optimizer.py  <-- Dijkstra on city graph\n"
        "|   |       |-- vision/\n"
        "|   |           |-- vehicle_detector.py <-- Vehicle counting\n"
        "|   |           |-- signal_detector.py  <-- Traffic light state\n"
        "|   |           |-- hawker_detector.py  <-- Hawker/obstruction alerts\n"
        "|   |           |-- illegal_parking_detector.py <-- LPR simulation\n"
        "|\n"
        "|-- frontend/\n"
        "|   |-- src/\n"
        "|   |   |-- main.jsx                   <-- FRONTEND ENTRY POINT\n"
        "|   |   |-- App.jsx                    <-- React Router (all routes)\n"
        "|   |   |-- pages/\n"
        "|   |   |   |-- Home.jsx               <-- Role selection portal\n"
        "|   |   |   |-- Dashboard.jsx          <-- Main traffic dashboard\n"
        "|   |   |   |-- EnforcementDashboard.jsx <-- Violation tracking\n"
        "|   |   |   |-- CitizenPWA.jsx         <-- Mobile citizen app\n"
        "|   |   |   |-- ParkingPage.jsx        <-- Smart parking view\n"
        "|   |   |   |-- Analytics.jsx          <-- Prediction & charts\n"
        "|   |   |   |-- MockDataViewer.jsx     <-- Raw data inspector\n"
        "|   |   |-- components/Dashboard/\n"
        "|   |   |   |-- TrafficMap.jsx         <-- Leaflet intersection map\n"
        "|   |   |   |-- AlertPanel.jsx         <-- Live security alerts\n"
        "|   |   |   |-- ExplainabilityPanel.jsx<-- AI decision reasoning\n"
        "|   |   |   |-- ParkingDashboard.jsx   <-- Parking charts + cards\n"
        "|   |   |   |-- ParkingMap.jsx         <-- Parking zone map\n"
        "|   |   |   |-- Chatbot.jsx            <-- AI chatbot widget\n"
        "|   |   |   |-- CameraFeed.jsx         <-- Live camera viewer\n"
        "|   |   |-- context/\n"
        "|   |       |-- AuthContext.jsx         <-- Role-based auth state\n"
        "|   |       |-- TrafficContext.jsx      <-- Real-time traffic data"
    )

    # ==================== 5. ARCHITECTURE ====================
    pdf.add_page()
    pdf.chapter_title("5. System Architecture & Services")

    pdf.section_title("Three Independent Services")
    pdf.table(
        ["Service", "Port", "Technology", "What It Does"],
        [
            ["Backend API", "8000", "FastAPI + Socket.IO", "Simulation, AI, APIs, WebSocket"],
            ["Camera Server", "5000", "Flask + OpenCV", "Real-time video processing"],
            ["Frontend", "3000", "React.js", "All UI dashboards & maps"],
        ],
        [35, 15, 50, 90]
    )

    pdf.section_title("How Services Communicate")
    pdf.code(
        "BROWSER (React @ 3000)\n"
        "  |-- REST API calls --> FastAPI Backend (8000)\n"
        "  |-- WebSocket (Socket.IO) <--> FastAPI Backend (8000)\n"
        "  |      [Receives traffic_update every 2 seconds]\n"
        "  |      [Receives hawker_alert on detection]\n"
        "  |\n"
        "  |-- WebSocket (Socket.IO) <--> Camera Server (5000)\n"
        "         [Receives detection_result per frame]\n"
        "\n"
        "MOBILE PHONE CAMERA\n"
        "  |-- Opens http://<PC-IP>:5000 in browser\n"
        "  |-- Streams video frames via Socket.IO\n"
        "  |-- Camera Server runs YOLO + OpenCV detection\n"
        "  |-- Emits hawker_alert / illegal_parking alerts"
    )

    # ==================== 6. EXECUTION FLOW ====================
    pdf.add_page()
    pdf.chapter_title("6. Application Execution Flow")

    pdf.section_title("Where Execution Starts")
    pdf.body("The project has TWO independent entry points that must both be running:")
    pdf.bullet("BACKEND: backend/app/main.py -- This is launched via uvicorn on port 8000.")
    pdf.bullet("FRONTEND: frontend/src/main.jsx -- This is launched via npm start on port 3000.")
    pdf.bullet("CAMERA (Optional): backend/app/services/mobile_camera/mobile_camera_server.py -- Port 5000.")

    pdf.section_title("Complete Execution Flow Diagram")
    pdf.code(
        "USER opens http://localhost:3000\n"
        "        |\n"
        "        v\n"
        "  [main.jsx] mounts <App /> into the DOM\n"
        "        |\n"
        "        v\n"
        "  [App.jsx] wraps everything in:\n"
        "    - AuthProvider (role management)\n"
        "    - ThemeProvider (dark mode)\n"
        "    - React Router (URL -> Page mapping)\n"
        "        |\n"
        "        v\n"
        "  Route '/' loads --> [Home.jsx]\n"
        "    - User sees 'UrbanFlow OS' branding\n"
        "    - User selects role from dropdown:\n"
        "        * Traffic Police\n"
        "        * Enforcement Dept\n"
        "        * City Admin\n"
        "        * Local Citizen\n"
        "    - User clicks 'Enter Dashboard'\n"
        "        |\n"
        "        v\n"
        "  AuthContext stores the role, Router navigates:\n"
        "    - Police/Admin  --> /dashboard  --> [Dashboard.jsx]\n"
        "    - Enforcement    --> /enforcement --> [EnforcementDashboard.jsx]\n"
        "    - Citizen         --> /citizen     --> [CitizenPWA.jsx]\n"
        "        |\n"
        "        v\n"
        "  Page loads, TrafficContext connects WebSocket to Backend\n"
        "        |\n"
        "        v\n"
        "  Backend receives first WS connection:\n"
        "    - main.py triggers broadcast_loop()\n"
        "    - Simulation starts: RL Agent begins optimizing signals\n"
        "    - Every 2 seconds: traffic_update pushed to all clients\n"
        "        |\n"
        "        v\n"
        "  Dashboard receives live data --> Updates Maps, Charts, Alerts"
    )

    # ==================== 7. PAGE-BY-PAGE FEATURES ====================
    pdf.add_page()
    pdf.chapter_title("7. Page-by-Page Feature Guide")

    # 7.1 Home
    pdf.section_title("7.1 Home Portal (Home.jsx)")
    pdf.body("URL: http://localhost:3000/")
    pdf.body("Purpose: The landing page and entry point for all users.")
    pdf.sub_section("Features on this page:")
    pdf.bullet("Gradient-styled 'UrbanFlow OS' branding with modern dark theme.")
    pdf.bullet("Role selection dropdown with 4 options: Traffic Police, Enforcement, Admin, Citizen.")
    pdf.bullet("'Enter Dashboard' button that routes to the correct dashboard based on chosen role.")
    pdf.sub_section("How it works:")
    pdf.bullet("AuthContext.jsx stores the selected role in React state.")
    pdf.bullet("handleEnter() checks the role and calls navigate('/dashboard'), navigate('/enforcement'), or navigate('/citizen').")

    # 7.2 Dashboard
    pdf.section_title("7.2 Traffic Police / Admin Dashboard (Dashboard.jsx)")
    pdf.body("URL: http://localhost:3000/dashboard")
    pdf.body("Purpose: The main control center -- real-time traffic monitoring and AI signal control.")
    pdf.sub_section("Features on this page:")
    pdf.bullet("TRAFFIC MAP (Leaflet): Interactive map of Solapur showing 4 intersections with color-coded signal indicators (red/green/yellow circles).")
    pdf.bullet("LIVE KPI CARDS: Animated counters showing: Total Intersections, Active Vehicles, Avg Wait Time, CO2 Saved.")
    pdf.bullet("SIGNAL CONTROL: Visual traffic signal indicators for each of the 4 intersections, updated in real-time.")
    pdf.bullet("ALERT PANEL (AlertPanel.jsx): Live feed of security alerts from hawker detection, illegal parking, and traffic anomalies.")
    pdf.bullet("EXPLAINABILITY PANEL (XAI): Shows WHY the A3C neural network chose a specific signal phase (e.g., 'Extended green due to 15+ vehicle queue on North lane').")
    pdf.bullet("CAMERA FEED: Embedded view of the live mobile camera stream from port 5000.")
    pdf.bullet("AI CHATBOT: Chat widget powered by the AI chatbot API for traffic-related queries.")
    pdf.bullet("WEATHER TOGGLE: Dropdown to switch simulation weather between Clear, Rain, and Fog.")
    pdf.bullet("EMERGENCY SIREN: Button to trigger emergency vehicle preemption (forces green for emergency path).")
    pdf.bullet("SIMULATION START/STOP: Controls to start or stop the traffic simulation loop.")
    pdf.sub_section("Backend connections:")
    pdf.bullet("WebSocket: Receives 'traffic_update' events every 2 seconds from simulation.py.")
    pdf.bullet("WebSocket: Receives 'hawker_alert' events from both camera server and anomaly detector.")
    pdf.bullet("REST API: POST /api/v1/simulation/start and /stop for simulation control.")
    pdf.bullet("REST API: POST /api/v1/simulation/weather for weather mode changes.")

    # 7.3 Enforcement
    pdf.section_title("7.3 Enforcement Dashboard (EnforcementDashboard.jsx)")
    pdf.body("URL: http://localhost:3000/enforcement")
    pdf.body("Purpose: Focused view for city enforcement teams to track violations and respond quickly.")
    pdf.sub_section("Features on this page:")
    pdf.bullet("ALERT PANEL: Same AlertPanel component as main dashboard -- shows hawker detections, illegal parking alerts with License Plate Recognition (LPR) data, and traffic anomalies.")
    pdf.bullet("PARKING OVERVIEW: Embedded ParkingDashboard showing zone occupancy and violations.")
    pdf.bullet("QUICK ACTIONS: Buttons for 'Mark Resolved', 'Dispatch Unit'.")
    pdf.sub_section("Backend connections:")
    pdf.bullet("WebSocket: Receives 'hawker_alert' events (including illegal parking with simulated plate numbers like 'MH 12 AB 1234').")
    pdf.bullet("REST API: GET /api/v1/parking/zones for parking zone data.")

    # 7.4 Parking
    pdf.section_title("7.4 Smart Parking Page (ParkingPage.jsx)")
    pdf.body("URL: http://localhost:3000/parking")
    pdf.body("Purpose: City-wide parking infrastructure management and prediction.")
    pdf.sub_section("Features on this page:")
    pdf.bullet("ZONE MAP (ParkingMap.jsx): Leaflet map with colored circle markers for each parking zone in Solapur. Green = available, Yellow = filling up, Red = full.")
    pdf.bullet("KPI CARDS: Total Zones, Total Capacity, Available Spots, Occupancy Rate -- with animated counters.")
    pdf.bullet("AI PREDICTION CHART (Recharts): 4-hour occupancy forecast powered by the XGBoost model. Shows predicted fill-up times.")
    pdf.bullet("ZONE DETAILS: Click any zone on the map to see detailed occupancy, type (on-street vs structured), and coordinates.")
    pdf.sub_section("Backend connections:")
    pdf.bullet("REST API: GET /api/v1/parking/zones -- Returns all parking zone data.")
    pdf.bullet("REST API: GET /api/v1/parking/predict/<zone_id> -- Returns XGBoost occupancy prediction.")
    pdf.bullet("WebSocket: Receives 'parking_update' events for real-time occupancy changes.")

    # 7.5 Analytics
    pdf.section_title("7.5 Analytics & Predictions (Analytics.jsx)")
    pdf.body("URL: http://localhost:3000/analytics")
    pdf.body("Purpose: Deep-dive into traffic predictions and environmental impact data.")
    pdf.sub_section("Features on this page:")
    pdf.bullet("WAIT TIME CHART: 24-hour forecast showing Baseline Wait Time vs AI-Optimized Wait Time. Data comes from the Prophet+LSTM traffic predictor API.")
    pdf.bullet("EMISSIONS CHART: CO2 emissions comparison showing environmental impact of AI optimization.")
    pdf.bullet("INTERSECTION COMPARISON: Side-by-side performance metrics for all 4 intersections.")
    pdf.sub_section("Backend connections:")
    pdf.bullet("REST API: GET /api/v1/prediction/forecast -- Returns 24-hour traffic forecast data.")

    # 7.6 Citizen PWA
    pdf.section_title("7.6 Citizen Mobile PWA (CitizenPWA.jsx)")
    pdf.body("URL: http://localhost:3000/citizen")
    pdf.body("Purpose: Mobile-friendly interface for regular citizens of Solapur.")
    pdf.sub_section("Features on this page:")
    pdf.bullet("MOBILE LAYOUT: Constrained to 480px width with a bottom navigation bar -- looks and feels like a native mobile app.")
    pdf.bullet("QUICK ACTION GRID: Buttons for Find Parking, Live Traffic, Report Issue, Transit Info.")
    pdf.bullet("PARKING STATUS: Pulls real-time parking zone data and displays nearest zones with color-coded capacity bars (green/yellow/red).")
    pdf.bullet("BOTTOM NAVIGATION: Home, Map, Alerts, Profile tabs -- mobile app style.")
    pdf.sub_section("Backend connections:")
    pdf.bullet("REST API: GET /api/v1/parking/zones -- Fetches live parking availability.")

    # 7.7 Camera
    pdf.section_title("7.7 Mobile Camera Server (http://localhost:5000)")
    pdf.body("URL: http://<your-PC-IP>:5000 (open on mobile phone, same Wi-Fi)")
    pdf.body("Purpose: Streams phone camera feed to the server for real-time computer vision analysis.")
    pdf.sub_section("Features:")
    pdf.bullet("CAMERA INTERFACE: Mobile-optimized HTML page with Start/Stop/Switch camera controls.")
    pdf.bullet("VEHICLE DETECTION: YOLOv8 counts vehicles and assigns them to lanes (N/S/E/W).")
    pdf.bullet("SIGNAL DETECTION: HSV color detection identifies traffic light state (Red/Yellow/Green).")
    pdf.bullet("HAWKER DETECTION: Identifies stationary objects blocking the road.")
    pdf.bullet("ILLEGAL PARKING: Detects vehicles parked in restricted zones, generates simulated license plate numbers.")
    pdf.bullet("RESULTS OVERLAY: Detection results shown directly on the phone screen in real-time.")

    # ==================== 8. BACKEND APIs ====================
    pdf.add_page()
    pdf.chapter_title("8. Backend API Endpoints")

    pdf.section_title("FastAPI Server (Port 8000)")
    pdf.table(
        ["Method", "Endpoint", "Description"],
        [
            ["GET", "/", "API health - returns running status"],
            ["GET", "/health", "Health check endpoint"],
            ["POST", "/api/v1/simulation/start", "Start the traffic simulation loop"],
            ["POST", "/api/v1/simulation/stop", "Stop the simulation"],
            ["GET", "/api/v1/simulation/status", "Get simulation state (running/stopped)"],
            ["POST", "/api/v1/simulation/weather", "Set weather: clear, rain, fog"],
            ["POST", "/api/v1/simulation/emergency", "Trigger emergency vehicle preemption"],
            ["GET", "/api/v1/parking/zones", "Get all parking zones with occupancy"],
            ["GET", "/api/v1/parking/predict/:id", "XGBoost occupancy prediction"],
            ["GET", "/api/v1/prediction/forecast", "24hr traffic flow forecast"],
            ["POST", "/api/v1/routing/optimize", "Dijkstra shortest path calculation"],
            ["POST", "/api/v1/chatbot/message", "Send a message to AI chatbot"],
            ["GET", "/api/v1/ml/status", "ML model status"],
        ],
        [18, 75, 97]
    )

    pdf.section_title("WebSocket Events (Port 8000)")
    pdf.table(
        ["Event", "Direction", "Data Sent"],
        [
            ["connect", "Client -> Server", "Client joins WebSocket room"],
            ["traffic_update", "Server -> Client", "All intersection states (every 2s)"],
            ["parking_update", "Server -> Client", "Parking zone occupancy changes"],
            ["hawker_alert", "Server -> Client", "Alert with message + severity"],
        ],
        [40, 45, 105]
    )

    pdf.section_title("Camera Server (Port 5000)")
    pdf.table(
        ["Method", "Endpoint", "Description"],
        [
            ["GET", "/", "Mobile camera HTML page"],
            ["GET", "/api/status", "Server status, FPS, frame count"],
            ["GET", "/api/latest", "Latest detection results JSON"],
            ["GET", "/api/rl_state", "RL state vector for agent"],
        ],
        [18, 55, 117]
    )

    # ==================== 9. AI/ML MODELS ====================
    pdf.add_page()
    pdf.chapter_title("9. AI/ML Models Used")

    pdf.table(
        ["Model", "Technology", "Purpose", "Input", "Output"],
        [
            ["A3C RL Agent", "PyTorch", "Signal optimization", "32-dim state vector", "Phase action (0-3)"],
            ["YOLOv8 Detector", "Ultralytics", "Vehicle detection", "Camera frame", "Bounding boxes"],
            ["XGBoost Predictor", "Scikit-learn", "Parking prediction", "Zone + time features", "Occupancy %"],
            ["Traffic Predictor", "Synthetic", "Traffic forecasting", "Historical patterns", "24hr forecast"],
            ["Anomaly Detector", "IsolationForest", "Unusual patterns", "Intersection metrics", "Anomaly alerts"],
            ["Hawker Detector", "OpenCV", "Road obstructions", "Camera frame", "Alert with severity"],
            ["Illegal Parking", "Custom", "Parking violations", "Vehicle positions", "LPR + alert"],
        ],
        [30, 28, 38, 42, 42]
    )

    pdf.section_title("How the A3C Agent Works")
    pdf.code(
        "State Vector (32 dims) --> Neural Network --> Action\n"
        "  [queue, vehicles,     [128 hidden     [0=Green\n"
        "   speed, phase          neurons          1=Yellow\n"
        "   x 4 intersections     + ReLU]          2=Red\n"
        "   + padding]                             3=Extended Green]\n"
        "\n"
        "Reward = -(waiting_time + 10 * stopped_vehicles)\n"
        "Goal: Minimize total wait time across all intersections"
    )

    # ==================== 10. DATA STRUCTURES ====================
    pdf.add_page()
    pdf.chapter_title("10. Data Structures (In-Memory Database)")

    pdf.body(
        "For hackathon speed, UrbanFlow uses in-memory Python dictionaries and lists instead of a "
        "traditional SQL database. All state is managed by SimulationManager and ParkingManager "
        "classes that broadcast via WebSocket every 2 seconds."
    )

    pdf.section_title("Intersection State (per intersection)")
    pdf.table(
        ["Field", "Type", "Example", "Description"],
        [
            ["id", "String", "INT_1", "Unique intersection ID"],
            ["name", "String", "Vijapur Rd-Station", "Human-readable name"],
            ["lat", "Float", "17.6599", "Latitude for map"],
            ["lng", "Float", "75.9064", "Longitude for map"],
            ["vehicles", "Int", "23", "Current vehicle count"],
            ["queue_length", "Int", "8", "Vehicles waiting in queue"],
            ["avg_speed", "Float", "12.5", "Average speed (km/h)"],
            ["avg_wait", "Float", "45.2", "Average wait time (sec)"],
            ["current_phase", "Int", "0", "0=Green, 1=Yellow, 2=Red"],
        ],
        [35, 20, 40, 95]
    )

    pdf.section_title("Parking Zone (per zone)")
    pdf.table(
        ["Field", "Type", "Example", "Description"],
        [
            ["zone_id", "String", "PZ_001", "Unique zone ID"],
            ["name", "String", "Station Road Lot", "Zone name"],
            ["total_capacity", "Int", "50", "Total parking slots"],
            ["occupied_slots", "Int", "35", "Currently occupied"],
            ["lat", "Float", "17.6650", "Zone latitude"],
            ["lng", "Float", "75.9100", "Zone longitude"],
            ["type", "String", "structured", "on-street or structured"],
        ],
        [35, 20, 45, 90]
    )

    # ==================== 11. KEY FEATURES ====================
    pdf.add_page()
    pdf.chapter_title("11. Key Features Summary")

    pdf.table(
        ["#", "Feature", "Technology Used"],
        [
            ["1", "Adaptive Traffic Signal Control", "A3C Reinforcement Learning (PyTorch)"],
            ["2", "Real-time Vehicle Detection", "YOLOv8 + OpenCV via Phone Camera"],
            ["3", "Smart Parking Management", "Zone Tracking + XGBoost Predictions"],
            ["4", "Hawker & Obstruction Detection", "Computer Vision (Stationary Object Detection)"],
            ["5", "Illegal Parking + LPR", "Vision Module + Mock License Plate Recognition"],
            ["6", "Traffic Flow Prediction", "Prophet + LSTM Hybrid 24hr Forecasting"],
            ["7", "Route Optimization", "NetworkX + Dijkstra Shortest Path"],
            ["8", "Anomaly Detection", "Scikit-learn Isolation Forest"],
            ["9", "Role-Based Access Control", "React AuthContext + 4 User Roles"],
            ["10", "Explainable AI (XAI)", "Decision Reasoning Panel on Dashboard"],
            ["11", "Weather & Event Integration", "Weather toggle + Emergency Siren trigger"],
            ["12", "Citizen Mobile PWA", "Mobile-responsive React page"],
            ["13", "AI Chatbot", "Natural language traffic assistant"],
            ["14", "CO2 Emissions Tracking", "Green impact metrics on dashboard"],
        ],
        [10, 80, 100]
    )

    # ==================== 12. FUTURE ENHANCEMENTS ====================
    pdf.chapter_title("12. Future Enhancements")
    pdf.bullet("PostgreSQL/PostGIS: Replace in-memory data with a persistent geospatial database for production.")
    pdf.bullet("Edge AI: Deploy detection models on Raspberry Pi / Jetson Nano at intersections for zero-latency computation.")
    pdf.bullet("V2X (Vehicle-to-Everything): Integrate with Google Maps API for citizen rerouting.")
    pdf.bullet("Mobile App: Convert CitizenPWA into a standalone React Native or Flutter application.")
    pdf.bullet("Multi-City Scaling: Federated learning to train across multiple city installations.")

    # ==================== 13. CONCLUSION ====================
    pdf.chapter_title("13. Conclusion")
    pdf.body(
        "UrbanFlow demonstrates how AI can transform traffic management for medium-sized Indian cities "
        "like Solapur. By combining Computer Vision, Reinforcement Learning, Predictive Analytics, and "
        "Role-Based Dashboards into a single platform, we eliminate the need for expensive hardware "
        "sensors. A regular smartphone camera becomes a smart traffic sensor, and the A3C AI brain "
        "optimizes signals in real-time -- reducing wait times by up to 30-40% compared to fixed timers."
    )
    pdf.body(
        "The system serves all city stakeholders: traffic police get live control, enforcement gets "
        "automated alerts, administrators get analytics, and citizens get a mobile app for parking and "
        "transit information. UrbanFlow proves that software-defined, AI-adaptive infrastructure is "
        "the future of smart city traffic management."
    )

    # ==================== SAVE ====================
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "UrbanFlow_Workflow_Documentation.pdf")
    pdf.output(output_path)
    print(f"\nPDF saved: {output_path}")
    print(f"Pages: {pdf.page_no()}")
    return output_path


if __name__ == "__main__":
    create_pdf()
