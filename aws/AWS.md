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
```

Private: 10.0.60.7
