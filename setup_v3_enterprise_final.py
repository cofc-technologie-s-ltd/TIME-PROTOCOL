import os

os.makedirs("services/iso20022", exist_ok=True)
os.makedirs("benchmarks/load", exist_ok=True)
os.makedirs("tests", exist_ok=True)

# 1. ISO 20022 Financial Messaging Engine
with open("services/iso20022/iso_gateway.py", "w", encoding="utf-8") as f:
    f.write('''import xml.etree.ElementTree as ET
import time
import uuid

class ISO20022Gateway:
    """
    ISO 20022 financial messaging standard implementation 
    for institutional cross-border payment instructions (pacs.008).
    """
    def __init__(self, institution_bic: str):
        self.bic = institution_bic

    def generate_pacs_008_credit_transfer(self, debtor: str, creditor: str, amount: float, currency: str = "USD") -> str:
        msg_id = str(uuid.uuid4())
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Constructing XML structure compliant with ISO 20022 standard
        root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.10")
        fi_to_fi = ET.SubElement(root, "FIToFIPmtStsRpt")
        
        grpHdr = ET.SubElement(fi_to_fi, "GrpHdr")
        ET.SubElement(grpHdr, "MsgId").text = msg_id
        ET.SubElement(grpHdr, "CreDtTm").text = timestamp
        
        txInf = ET.SubElement(fi_to_fi, "TxInfAndSts")
        amt_elem = ET.SubElement(txInf, "IntrBkSttlmAmt", Ccy=currency)
        amt_elem.text = f"{amount:.2f}"
        
        dbtr = ET.SubElement(txInf, "Dbtr")
        ET.SubElement(dbtr, "Name").text = debtor
        
        cdtr = ET.SubElement(txInf, "Cdtr")
        ET.SubElement(cdtr, "Name").text = creditor

        return ET.tostring(root, encoding='utf-8').decode('utf-8')
''')

# 2. k6 Load Testing Script
with open("benchmarks/load/k6_load_test.js", "w", encoding="utf-8") as f:
    f.write('''import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '30s', target: 50 },   // Ramp up
        { duration: '1m', target: 200 },   // Steady state
        { duration: '30s', target: 0 },    // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<300'],  // 95% under 300ms
        http_req_failed: ['rate<0.01'],    // <1% errors
    },
};

export default function () {
    const res = http.get('http://127.0.0.1:8080/api/status');
    check(res, {
        'status is 200': (r) => r.status === 200,
        'response valid': (r) => r.json('status') === 'ok',
    });
    sleep(1);
}
''')

# 3. Add ISO Gateway Unit Test
with open("tests/test_iso_gateway.py", "w", encoding="utf-8") as f:
    f.write('''import unittest
from services.iso20022.iso_gateway import ISO20022Gateway

class TestISOGateway(unittest.TestCase):
    def test_pacs_008_generation(self):
        iso = ISO20022Gateway("TIMEIL01XXX")
        xml_msg = iso.generate_pacs_008_credit_transfer("Alice", "Bob", 15000.00, "USD")
        self.assertIn("pacs.008.001.10", xml_msg)
        self.assertIn("Alice", xml_msg)
        self.assertIn("15000.00", xml_msg)

if __name__ == "__main__":
    unittest.main()
''')

print("[+] Successfully generated ISO 20022 Gateway, k6 Load Tests, and Unit Tests!")
