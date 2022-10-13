import os.environ

#===DEBUG print function
def debug(text):
    if int(os.environ.get("DEBUG", 0)):
        print(text)