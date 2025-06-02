#COPY NEEDED FILES
scp -i ~/.ssh/id_ed25519 -r ./requirements.txt ubuntu@ec2-13-219-246-81.compute-1.amazonaws.com:~/code
scp -i ~/.ssh/id_ed25519 -r Dockerfile ubuntu@ec2-13-219-246-81.compute-1.amazonaws.com:~/code

rsync -avz -e "ssh -i ~/.ssh/id_ed25519" --exclude='__pycache__' ./app/ ubuntu@ec2-13-219-246-81.compute-1.amazonaws.com:~/code/app

#ENTER THE MACHINE
ssh -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 ubuntu@ec2-13-219-246-81.compute-1.amazonaws.com << 'EOF'

#RUN ALL COMMANDS INSIDE MACHINE

#INSTALL DOCKER
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

sudo usermod -aG docker $USER

EOF

ssh -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 ubuntu@ec2-13-219-246-81.compute-1.amazonaws.com << 'EOF'
cd ~/code
docker build -t my-api .
EOF