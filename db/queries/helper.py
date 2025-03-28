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