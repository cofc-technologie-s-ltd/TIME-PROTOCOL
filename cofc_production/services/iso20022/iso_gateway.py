import xml.etree.ElementTree as ET
import uuid
import time

class ProductionISOGateway:
    def __init__(self, bic: str):
        self.bic = bic

    def generate_pacs_008(self, debtor: str, creditor: str, amount: float, ccy: str = "USD") -> str:
        root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.10")
        fi = ET.SubElement(root, "FIToFIPmtStsRpt")
        hdr = ET.SubElement(fi, "GrpHdr")
        ET.SubElement(hdr, "MsgId").text = str(uuid.uuid4())
        ET.SubElement(hdr, "CreDtTm").text = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        tx = ET.SubElement(fi, "TxInfAndSts")
        amt = ET.SubElement(tx, "IntrBkSttlmAmt", Ccy=ccy)
        amt.text = f"{amount:.2f}"
        dbtr = ET.SubElement(tx, "Dbtr")
        ET.SubElement(dbtr, "Name").text = debtor
        cdtr = ET.SubElement(tx, "Cdtr")
        ET.SubElement(cdtr, "Name").text = creditor
        return ET.tostring(root, encoding='utf-8').decode('utf-8')
