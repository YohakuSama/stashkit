"""DNS failures and malformed messages must never be reported as PASS."""
import copy
import struct
import sys
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import dns.flags
import dns.message
import dns.rcode
import dns.rrset

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_dns_endpoint import make_query, validate_dns_response, NoRedirect


class DNSProbeTests(unittest.TestCase):
    def setUp(self):
        self.query = make_query()
        self.response = dns.message.make_response(self.query)
        self.response.answer.append(dns.rrset.from_text("example.com.", 300, "IN", "A", "93.184.215.14"))

    def test_valid_a_answer(self):
        self.assertEqual(validate_dns_response(self.response.to_wire(), self.query), ["93.184.215.14"])

    def test_valid_cname_chain(self):
        self.response.answer = [
            dns.rrset.from_text("example.com.", 300, "IN", "CNAME", "alias.example.net."),
            dns.rrset.from_text("alias.example.net.", 300, "IN", "A", "93.184.215.14"),
        ]
        self.assertEqual(validate_dns_response(self.response.to_wire(), self.query), ["93.184.215.14"])

    def test_old_twelve_byte_false_positive_rejected(self):
        wire = struct.pack("!6H", 0x3107, 0x8002, 1, 0, 0, 0)
        with self.assertRaises(ValueError):
            validate_dns_response(wire, self.query)

    def test_error_response_codes_rejected(self):
        for code in (dns.rcode.SERVFAIL, dns.rcode.NXDOMAIN, dns.rcode.REFUSED):
            with self.subTest(code=code):
                self.response.set_rcode(code)
                with self.assertRaisesRegex(ValueError, "query failed"):
                    validate_dns_response(self.response.to_wire(), self.query)

    def test_wrong_id_rejected(self):
        self.response.id += 1
        with self.assertRaisesRegex(ValueError, "ID mismatch"):
            validate_dns_response(self.response.to_wire(), self.query)

    def test_wrong_question_rejected(self):
        self.response.question = dns.message.make_query("other.example", "A").question
        with self.assertRaisesRegex(ValueError, "question mismatch"):
            validate_dns_response(self.response.to_wire(), self.query)

    def test_no_question_rejected(self):
        self.response.question = []
        with self.assertRaisesRegex(ValueError, "question mismatch"):
            validate_dns_response(self.response.to_wire(), self.query)

    def test_empty_or_unrelated_answer_rejected(self):
        for answers in ([], [dns.rrset.from_text("other.example.", 300, "IN", "A", "93.184.215.14")]):
            with self.subTest(answers=answers):
                self.response.answer = answers
                with self.assertRaisesRegex(ValueError, "no final A answer"):
                    validate_dns_response(self.response.to_wire(), self.query)

    def test_private_address_rejected(self):
        self.response.answer = [dns.rrset.from_text("example.com.", 300, "IN", "A", "127.0.0.1")]
        with self.assertRaisesRegex(ValueError, "non-public"):
            validate_dns_response(self.response.to_wire(), self.query)

    def test_query_packet_rejected(self):
        with self.assertRaisesRegex(ValueError, "standard DNS response"):
            validate_dns_response(self.query.to_wire(), self.query)

    def test_truncation_and_trailing_data_rejected(self):
        wire = self.response.to_wire()
        truncated = copy.deepcopy(self.response)
        truncated.flags |= dns.flags.TC
        for payload in (wire[:-1], wire + b"unexpected", truncated.to_wire()):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    validate_dns_response(payload, self.query)

    def test_redirect_rejected_instead_of_querying_another_endpoint(self):
        request = urllib.request.Request("https://223.5.5.5/dns-query?dns=test")
        with self.assertRaises(urllib.error.HTTPError):
            NoRedirect().redirect_request(request, None, 302, "Found", {}, "http://example.net/dns-query")


if __name__ == "__main__":
    unittest.main()
