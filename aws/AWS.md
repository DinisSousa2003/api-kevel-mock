# Container instances

3 m7i.large instances

ec2-13-219-246-81.compute-1.amazonaws.com
ec2-44-222-181-38.compute-1.amazonaws.com
ec2-44-202-179-1.compute-1.amazonaws.com

## FASTAPI
ssh -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 ubuntu@ec2-13-219-246-81.compute-1.amazonaws.com \\
10.0.63.154 172.17.0.1 

### Structure
code -> Dockerfile, /app, requirements.txt, /envs

## DATABASE
ssh -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 ubuntu@ec2-44-222-181-38.compute-1.amazonaws.com
10.0.53.50

### Structure
code -> Dockerfile, app, requirements.txt

## LOCUST
ssh -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 ubuntu@ec2-44-202-179-1.compute-1.amazonaws.com
10.0.60.7 

- [x] Server running
- [x] Pinging from other EC2 instance to server
- [ ] Connect server with database
- 