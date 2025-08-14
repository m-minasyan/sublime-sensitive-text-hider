import unittest
import sys
import os
import json
import tempfile
import re
from unittest.mock import patch, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'standalone-script'))

from sensitive_text_processor import (
    DEFAULT_PATTERNS,
    hide_sensitive_text,
    reveal_sensitive_text,
    load_custom_patterns
)

class TestEdgeCasesPatternDetection(unittest.TestCase):
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
    
    def tearDown(self):
        for ext in ['', '.sensitive_backup', '.sensitive_map']:
            file_path = self.temp_file_path + ext
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def test_malformed_email_addresses(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Invalid: @example.com, test@, test@.com")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertNotIn("${EMAIL}", content)
        self.assertIn("@example.com", content)
        self.assertIn("test@", content)
    
    def test_partial_credit_card_numbers(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Short cards: 1234 5678, 123456789012345 (15 digits), 12345678901234567 (17 digits)")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertNotIn("${CREDIT_CARD}", content)
        self.assertIn("1234 5678", content)
        self.assertIn("123456789012345", content)
        self.assertIn("12345678901234567", content)
    
    def test_invalid_ssn_formats(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Invalid SSNs: 12-345-6789, 1234-56-789, 123-4-56789, 000-00-0000")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("000-00-0000", content)
        self.assertIn("12-345-6789", content)
        self.assertIn("1234-56-789", content)
    
    def test_out_of_range_ip_addresses(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Invalid IPs: 256.256.256.256, 999.999.999.999, 355.355.355.355")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertNotIn("${IP_ADDRESS}", content)
        self.assertIn("256.256.256.256", content)
        self.assertIn("999.999.999.999", content)
        self.assertIn("355.355.355.355", content)
    
    def test_edge_boundary_ip_addresses(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Edge IPs: 0.0.0.0, 255.255.255.255, 1.1.1.1, 254.254.254.254")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content.count("${IP_ADDRESS}"), 4)
        self.assertNotIn("0.0.0.0", content)
        self.assertNotIn("255.255.255.255", content)
    
    def test_mixed_case_api_keys(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Keys: Api_Key_ABC123def456GHI789, API-KEY-xyz789ABC123def456")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content.count("${API_KEY}"), 2)
        self.assertNotIn("Api_Key_ABC123def456GHI789", content)
        self.assertNotIn("API-KEY-xyz789ABC123def456", content)
    
    def test_unicode_in_patterns(self):
        with open(self.temp_file_path, 'w', encoding='utf-8') as f:
            f.write("Unicode emails: test@example.com, user@domain.org")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertEqual(content.count("${EMAIL}"), 2)
    
    def test_overlapping_patterns(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Overlap: password=123-45-6789")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertTrue("${PASSWORD}" in content or "${SSN}" in content)
    
    def test_nested_quotes_in_passwords(self):
        with open(self.temp_file_path, 'w') as f:
            f.write('Nested: password="contains\\"quotes\\"inside", PASSWORD=\'single\\\'quote\\\'\'')
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("${PASSWORD}", content)
    
    def test_multiline_patterns(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("""Email split
across lines: test@
example.com
Credit card: 1234
5678 9012 3456""")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("test@", content)
        self.assertNotIn("${EMAIL}", content)
    
    def test_consecutive_sensitive_data(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("test@example.com john@doe.org 192.168.1.1 123-45-6789")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content.count("${EMAIL}"), 2)
        self.assertIn("${IP_ADDRESS}", content)
        self.assertIn("${SSN}", content)
    
    def test_special_characters_in_context(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Special: $test@example.com$ [192.168.1.1] {123-45-6789}")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("${EMAIL}", content)
        self.assertIn("${IP_ADDRESS}", content)
        self.assertIn("${SSN}", content)
        self.assertIn("$", content)
        self.assertIn("[", content)
        self.assertIn("]", content)
    
    def test_empty_file_handling(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content, "")
        self.assertFalse(os.path.exists(self.temp_file_path + '.sensitive_backup'))
    
    def test_whitespace_only_file(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("   \n\t\n   \t   ")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content, "   \n\t\n   \t   ")
        self.assertFalse(os.path.exists(self.temp_file_path + '.sensitive_backup'))
    
    def test_api_key_length_variations(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Short: API_KEY_abc123, Long: API_KEY_" + "a" * 100 + ", Normal: API_KEY_abcdef1234567890")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("API_KEY_abc123", content)
        self.assertIn("${API_KEY}", content)
        self.assertNotIn("API_KEY_abcdef1234567890", content)

class TestPatternValidationEdgeCases(unittest.TestCase):
    
    def test_invalid_regex_pattern(self):
        patterns_data = [
            {
                'pattern': r'[invalid(regex',
                'replacement': '${INVALID}'
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(patterns_data, f)
            patterns_file = f.name
        
        try:
            with self.assertRaises(re.error):
                patterns = load_custom_patterns(patterns_file)
                re.compile(patterns[0]['pattern'])
        finally:
            os.remove(patterns_file)
    
    def test_empty_pattern(self):
        patterns_data = [
            {
                'pattern': '',
                'replacement': '${EMPTY}'
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(patterns_data, f)
            patterns_file = f.name
        
        try:
            patterns = load_custom_patterns(patterns_file)
            self.assertEqual(patterns[0]['pattern'], '')
        finally:
            os.remove(patterns_file)
    
    def test_pattern_with_lookahead_lookbehind(self):
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        temp_file_path = temp_file.name
        temp_file.close()
        
        try:
            with open(temp_file_path, 'w') as f:
                f.write("secret123 public123 secret456")
            
            custom_patterns = [
                {'pattern': r'(?<=secret)\d+', 'replacement': '${SECRET_NUM}'}
            ]
            
            hide_sensitive_text(temp_file_path, custom_patterns)
            
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            self.assertIn("secret${SECRET_NUM}", content)
            self.assertIn("public123", content)
        finally:
            for ext in ['', '.sensitive_backup', '.sensitive_map']:
                file_path = temp_file_path + ext
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    def test_pattern_with_backreferences(self):
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        temp_file_path = temp_file.name
        temp_file.close()
        
        try:
            with open(temp_file_path, 'w') as f:
                f.write("repeated: 123-123, different: 123-456")
            
            custom_patterns = [
                {'pattern': r'(\d{3})-\1', 'replacement': '${REPEATED}'}
            ]
            
            hide_sensitive_text(temp_file_path, custom_patterns)
            
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            self.assertIn("${REPEATED}", content)
            self.assertIn("123-456", content)
        finally:
            for ext in ['', '.sensitive_backup', '.sensitive_map']:
                file_path = temp_file_path + ext
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    def test_case_insensitive_flag_edge_cases(self):
        patterns_data = [
            {
                'pattern': r'password',
                'replacement': '${PWD}',
                'flags': 'IGNORECASE'
            }
        ]
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        temp_file_path = temp_file.name
        temp_file.close()
        
        try:
            with open(temp_file_path, 'w') as f:
                f.write("PASSWORD Password password PaSsWoRd")
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as pf:
                json.dump(patterns_data, pf)
                patterns_file = pf.name
            
            patterns = load_custom_patterns(patterns_file)
            hide_sensitive_text(temp_file_path, patterns)
            
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            self.assertEqual(content.count("${PWD}"), 4)
            self.assertNotIn("PASSWORD", content)
            self.assertNotIn("password", content)
            self.assertNotIn("PaSsWoRd", content)
        finally:
            os.remove(patterns_file)
            for ext in ['', '.sensitive_backup', '.sensitive_map']:
                file_path = temp_file_path + ext
                if os.path.exists(file_path):
                    os.remove(file_path)

if __name__ == '__main__':
    unittest.main()