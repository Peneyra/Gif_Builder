with open("./subject.eml",'r') as file:
    stuff = file.read()
    for s in stuff.splitlines():
        print(s)
    exit