import subprocess


def readable_size(num_bytes: int) -> str:
    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == 'TiB':
            if unit == 'B':
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024


def merge_with_past(past, attributes, rules):
    for (attr, value) in attributes.items():
        rule = rules[attr]

        #More recent than past
        if rule == "most-recent":
            past[attr] = value

        #If exists, is older, else update
        elif rule == "older":
            past[attr] = past.get(attr, value)
            
        #Get value and sum
        elif rule == "sum":
            past[attr] = past.get(attr, 0) + value

        #Update if value > current
        elif rule == "max":
            past[attr] = max(past.get(attr, float('-inf')), value)

        #Logical OR
        elif rule == "or":
            past[attr] = value or past.get(attr, False)

    return past

def merge_with_future(future, attributes, rules):
    for (attr, value) in attributes.items():
        rule = rules[attr]

         #Value if value does not exist (future is more recent)
        if rule == "most-recent":
            future['attributes'][attr] = future['attributes'].get(attr, value)
        
        #Value is always older than future
        elif rule == "older":
            future['attributes'][attr] = value
            
        #Add value to the attributes
        elif rule == "sum":
            future['attributes'][attr] = (future['attributes'].get(attr, 0)) + value

        #Update if value > current
        elif rule == "max":
            future['attributes'][attr] = max(future['attributes'].get(attr, float('-inf')), value)

        #Or between current and value
        elif rule == "or":
            future['attributes'][attr] = value or future['attributes'].get(attr, False)

    return future

def get_size_script(database_name):
    size_dict = dict()

    if database_name not in ["postgres", "terminus", "xtdb2"]:
        print(f"[ERROR]: {database_name}] Bad name ")
        return size_dict

    # Run remote shell script via subprocess
    try:
        result = subprocess.check_output(
            [
                "bash", f"scripts/get-size-{database_name}.sh"
            ],
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in result.strip().split("\n"):
            if "=" in line:
                key, val = line.strip().split("=", 1)
                size_dict[key] = readable_size(int(val))

    except subprocess.CalledProcessError as e:
        print(f"[ERROR]: {database_name} Failed to get size info: {e.output.strip()}")
    except FileNotFoundError:
        print(f"[ERROR]: {database_name}] Script not found ")

    return size_dict


def du(path):
    try:
        output = subprocess.check_output(["du", "-sb", path], text=True)
        size_bytes = int(output.split()[0])
        return size_bytes
    except subprocess.CalledProcessError:
        return 0
    except FileNotFoundError:
        return 0
    
def docker_du(docker, path, args="-sb", pattern=None, multiply=1):
    try:
        if pattern:
            cmd = [
                "docker", "run", "--rm", "-v", docker,
                "alpine", "sh", "-c",
                f"du -ba {path} | grep '{pattern}' | awk '{{sum += $1}} END {{print sum}}'"
            ]
        else:
            cmd = [
                "docker", "run", "--rm", "-v", docker,
                "alpine", "du", args, path
            ]
        output = subprocess.check_output(cmd, text=True)
        size_bytes = int(output.split()[0]) * multiply
        return size_bytes
    except subprocess.CalledProcessError:
        return 0
    except FileNotFoundError:
        return 0
