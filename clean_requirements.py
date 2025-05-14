with open("requirements.txt", "r") as file:
    lines = file.readlines()

with open("requirements.txt", "w") as file:
    for line in lines:
        if "secondbrain" not in line:
            file.write(line)
