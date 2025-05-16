import os
import subprocess
import webbrowser
import time
import sys
import platform

# Set the Neon PostgreSQL database URL
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_E3By5fYHDgak@ep-silent-fog-a48gwvbn-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

def is_port_in_use(port):
    """Check if a port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_streamlit():
    """Start the Streamlit app on port 5000."""
    print("Starting ProductPulse on port 5000...")
    
    # Check if port 5000 is already in use
    if is_port_in_use(5000):
        print("Port 5000 is already in use. ProductPulse might already be running.")
        return
    
    # Command to run Streamlit on port 5000
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port=5000"]
    
    # Use subprocess to run the command
    try:
        # For Windows, use shell=True to properly handle executable paths
        use_shell = platform.system() == "Windows"
        process = subprocess.Popen(cmd, shell=use_shell)
        
        # Wait a moment for the app to start
        time.sleep(2)
        
        # Open the access page in the default browser
        webbrowser.open('http://localhost:5000')
        print("ProductPulse is now running on http://localhost:5000")
        
        # Keep the script running to maintain the Streamlit process
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nShutting down ProductPulse...")
            process.terminate()
            process.wait()
            print("ProductPulse has been shut down.")
    
    except Exception as e:
        print(f"Error starting ProductPulse: {e}")

if __name__ == "__main__":
    print("ProductPulse Analytics Dashboard")
    print("===============================")
    start_streamlit() 