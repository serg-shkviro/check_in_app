from suds.client import Client
import ssl

# Ignore SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

# Configure SOAP client
client = Client('http://localhost:8001/wsdl')

# Call SOAP endpoint
result = client.service.GetRandomLocation()
print(f"Random Location: Latitude={result.latitude}, Longitude={result.longitude}")
