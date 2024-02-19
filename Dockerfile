# Use Python 3.12 as the base image
FROM python:3.12

# Install system packages
COPY build/packages.txt /tmp/packages.txt
RUN apt-get clean && \
	apt-get update && \
    xargs -a /tmp/packages.txt apt-get install -y && \
    rm /tmp/packages.txt

# Install Python dependencies
COPY build/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Setup SSH server
RUN mkdir /var/run/sshd

# Expose the SSH and JupyterLab ports
EXPOSE 22
EXPOSE 8888

# Set SSH to listen on port 22 (you can change this port if you want)
RUN sed -i 's/#Port 22/Port 22/g' /etc/ssh/sshd_config

# Disable password authentication and use keys only
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/g' /etc/ssh/sshd_config

# Add your public key
RUN mkdir -p /root/.ssh
COPY build/dev_machine_key_pair.pub /root/.ssh/authorized_keys

# Start SSH and JupyterLab services
COPY build/startup.sh /root/startup.sh
RUN chmod +x /root/startup.sh
CMD ["/bin/sh", "-c", "/root/startup.sh && tail -f /dev/null"]