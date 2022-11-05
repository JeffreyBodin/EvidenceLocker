from os import environ

#===DEBUG print function
def debug(text):
    if int(environ.get("DEBUG", 0)):
        print(text)