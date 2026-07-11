def get_users():
    '''调用 GET /users'''
    import requests
    url = "http://localhost:8000/users"
    return requests.request("GET", url)
