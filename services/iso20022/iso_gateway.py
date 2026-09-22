import xml.etree.ElementTree as ET
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
