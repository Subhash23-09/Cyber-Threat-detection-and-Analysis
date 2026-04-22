
import os
from datetime import datetime, timedelta

def generate_ddos_log():
    log_file = "ddos_test.log"
    target_ip = "192.168.1.100"
    attacker_ip = "45.33.22.11" # Random public IP
    
    with open(log_file, "w") as f:
        # Start time
        base_time = datetime.utcnow()
        
        # burst of 1500 requests in 1 minute
        for i in range(1500):
            timestamp = (base_time + timedelta(milliseconds=i*20)).strftime("%b %d %H:%M:%S")
            # Log format: Timestamp Host Process: Message
            # Ensuring it hits the HTTP regex: (GET|POST|HEAD|PUT|DELETE)\s+
            # And has an IP
            line = f"{timestamp} firewall apache-access[100]: [{attacker_ip}] GET /index.php?id={i} HTTP/1.1 200 4523\n"
            f.write(line)

    print(f"Generated {log_file} with 1500 lines.")

if __name__ == "__main__":
    generate_ddos_log()
