# Container instances

3 m7i.large instances

ec2-13-219-246-81.compute-1.amazonaws.com
ec2-44-222-181-38.compute-1.amazonaws.com
ec2-44-202-179-1.compute-1.amazonaws.com

## SERVER FASTAPI

```bash
ssh -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 ubuntu@ec2-13-219-246-81.compute-1.amazonaws.com
```

Private: 10.0.63.154

### Structure-SERVER

code -> Dockerfile, /app, requirements.txt, /envs

## DATABASE

```bash
ssh -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 ubuntu@ec2-44-222-181-38.compute-1.amazonaws.com
```

Private: 10.0.53.50

### Structure-DATABASE

code -> Dockerfile, app, requirements.txt

## LOCUST

```bash
ssh -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 ubuntu@ec2-44-202-179-1.compute-1.amazonaws.com

locust_command = [
    "docker", "run", "--rm",
    "locust",
    "-f", "locusttest-aws.py",  # already in the container
    "--run-time", f"{tt}m",
    "--mode", mode,
    "--pct-get", str(pct_get),
    "--pct-get-now", str(pct_now),
    "--db", database,
    "--time", str(tt),
    "--user-number", str(users),
    "--rate", str(rate),
    "--host", "http://127.0.0.1:8000"
]
```

Private: 10.0.60.7

### TODO

- [x] Server running
- [x] Pinging from other EC2 instance to server
- [x] Connect server with database
- [x] Sending requests from my computer
