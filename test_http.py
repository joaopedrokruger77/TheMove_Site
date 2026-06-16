import requests
print("Fazendo GET para /confirmar/254...")
try:
    # Need to pass session cookie, but let's just see if we can hit the server.
    # Actually, if we don't have session cookie, it redirects to login.
    pass
except Exception as e:
    print(e)
