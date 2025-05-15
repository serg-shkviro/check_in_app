from app import create_app
from flask_jwt_extended import JWTManager
from app.settings import CheckinSettings
import random
from suds.client import Client
from http.client import HTTPSConnection
import ssl
from wsgiref.simple_server import make_server
import threading

# Flask app setup
app = create_app()
app.config['JWT_SECRET_KEY'] = CheckinSettings.JWT_SECRET
jwt = JWTManager(app)

# SOAP service
def soap_service(environ, start_response):
    wsdl = """<?xml version="1.0"?>
    <wsdl:definitions name="LocationService"
                      targetNamespace="http://example.com/locationservice"
                      xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
                      xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                      xmlns:tns="http://example.com/locationservice"
                      xmlns:xsd="http://www.w3.org/2001/XMLSchema">
        <wsdl:types>
            <xsd:schema targetNamespace="http://example.com/locationservice">
                <xsd:element name="GetRandomLocationResponse">
                    <xsd:complexType>
                        <xsd:sequence>
                            <xsd:element name="latitude" type="xsd:float"/>
                            <xsd:element name="longitude" type="xsd:float"/>
                        </xsd:sequence>
                    </xsd:complexType>
                </xsd:element>
            </xsd:schema>
        </wsdl:types>
        <wsdl:message name="GetRandomLocationResponse">
            <wsdl:part name="parameters" element="tns:GetRandomLocationResponse"/>
        </wsdl:message>
        <wsdl:portType name="LocationServicePortType">
            <wsdl:operation name="GetRandomLocation">
                <wsdl:output message="tns:GetRandomLocationResponse"/>
            </wsdl:operation>
        </wsdl:portType>
        <wsdl:binding name="LocationServiceBinding" type="tns:LocationServicePortType">
            <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
            <wsdl:operation name="GetRandomLocation">
                <soap:operation soapAction="GetRandomLocation"/>
                <wsdl:output>
                    <soap:body use="literal"/>
                </wsdl:output>
            </wsdl:operation>
        </wsdl:binding>
        <wsdl:service name="LocationService">
            <wsdl:port name="LocationServicePort" binding="tns:LocationServiceBinding">
                <soap:address location="http://0.0.0.0:8000/soap"/>
            </wsdl:port>
        </wsdl:service>
    </wsdl:definitions>"""

    if environ['PATH_INFO'] == '/wsdl':
        start_response('200 OK', [('Content-Type', 'text/xml')])
        return [wsdl.encode('utf-8')]

    # Handle SOAP request
    latitude = random.uniform(-90, 90)
    longitude = random.uniform(-180, 180)
    response = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://example.com/locationservice">
        <soap:Body>
            <tns:GetRandomLocationResponse>
                <latitude>{latitude}</latitude>
                <longitude>{longitude}</longitude>
            </tns:GetRandomLocationResponse>
        </soap:Body>
    </soap:Envelope>"""
    
    start_response('200 OK', [('Content-Type', 'text/xml')])
    return [response.encode('utf-8')]

# Run SOAP server in a separate thread
def run_soap_server():
    soap_server = make_server('0.0.0.0', 8000, soap_service)
    soap_server.serve_forever()

if __name__ == '__main__':
    # Start SOAP server in a thread
    soap_thread = threading.Thread(target=run_soap_server, daemon=True)
    soap_thread.start()
    
    # Run Flask app with gunicorn
    from gunicorn.app.base import BaseApplication
    
    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    options = {
        'bind': '0.0.0.0:5000',
        'workers': 2,
        'certfile': '/app/certs/cert.pem',
        'keyfile': '/app/certs/key.pem'
    }
    StandaloneApplication(app, options).run()
