from app.core.context.models import Endpoint, HTTPMethod


endpoint = Endpoint(path="/user",method=HTTPMethod.GET,description="get all user")


print(endpoint)
print(endpoint.method=="GET")