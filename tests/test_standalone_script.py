import unittest
import sys
import os
import json
import tempfile
import re
from unittest.mock import patch, mock_open, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'standalone-script'))

from sensitive_text_processor import (
    DEFAULT_PATTERNS,
    hide_sensitive_text,
    reveal_sensitive_text,
    load_custom_patterns,
    main
)

class TestHideSensitiveText(unittest.TestCase):
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
    
    def tearDown(self):
        for ext in ['', '.sensitive_backup', '.sensitive_map']:
            file_path = self.temp_file_path + ext
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def test_hide_email_addresses(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Contact: john@example.com and jane.doe@company.org")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("${EMAIL}", content)
        self.assertNotIn("john@example.com", content)
        self.assertNotIn("jane.doe@company.org", content)
        
        self.assertTrue(os.path.exists(self.temp_file_path + '.sensitive_backup'))
        self.assertTrue(os.path.exists(self.temp_file_path + '.sensitive_map'))
    
    def test_hide_credit_card_numbers(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Cards: 1234-5678-9012-3456 and 1111 2222 3333 4444")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("${CREDIT_CARD}", content)
        self.assertNotIn("1234-5678-9012-3456", content)
        self.assertNotIn("1111 2222 3333 4444", content)
    
    def test_hide_ssn(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("SSN: 123-45-6789 and 987-65-4321")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("${SSN}", content)
        self.assertNotIn("123-45-6789", content)
        self.assertNotIn("987-65-4321", content)
    
    def test_hide_ip_addresses(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("IPs: 192.168.1.1, 10.0.0.1, 255.255.255.255")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content.count("${IP_ADDRESS}"), 3)
        self.assertNotIn("192.168.1.1", content)
        self.assertNotIn("10.0.0.1", content)
        self.assertNotIn("255.255.255.255", content)
    
    def test_hide_api_keys(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("API_KEY_abcdef1234567890ghijklmnop and api-key-xyz123456789012345678901234")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("${API_KEY}", content)
        self.assertNotIn("API_KEY_abcdef1234567890ghijklmnop", content)
        self.assertNotIn("api-key-xyz123456789012345678901234", content)
    
    def test_hide_passwords(self):
        with open(self.temp_file_path, 'w') as f:
            f.write('password: "secret123" and PASSWORD=mysecret')
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content.count("${PASSWORD}"), 2)
        self.assertNotIn("password: \"secret123\"", content)
        self.assertNotIn("PASSWORD=mysecret", content)
    
    def test_no_sensitive_text(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("This is just normal text without any sensitive information")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content, "This is just normal text without any sensitive information")
        self.assertFalse(os.path.exists(self.temp_file_path + '.sensitive_backup'))
        self.assertFalse(os.path.exists(self.temp_file_path + '.sensitive_map'))
    
    def test_custom_patterns(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Custom data: ABC123 and XYZ789")
        
        custom_patterns = [
            {'pattern': r'\b[A-Z]{3}\d{3}\b', 'replacement': '${CUSTOM_ID}'}
        ]
        
        hide_sensitive_text(self.temp_file_path, custom_patterns)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("${CUSTOM_ID}", content)
        self.assertNotIn("ABC123", content)
        self.assertNotIn("XYZ789", content)
    
    def test_mapping_file_content(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Email: test@example.com")
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path + '.sensitive_map', 'r') as f:
            mappings = json.load(f)
        
        self.assertEqual(len(mappings), 1)
        self.assertEqual(mappings[0]['original'], 'test@example.com')
        self.assertEqual(mappings[0]['replacement'], '${EMAIL}')
        self.assertIn('start', mappings[0])
        self.assertIn('end', mappings[0])

class TestRevealSensitiveText(unittest.TestCase):
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
    
    def tearDown(self):
        for ext in ['', '.sensitive_backup', '.sensitive_map']:
            file_path = self.temp_file_path + ext
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def test_reveal_hidden_text(self):
        original_content = "Email: test@example.com, SSN: 123-45-6789"
        with open(self.temp_file_path, 'w') as f:
            f.write(original_content)
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            hidden_content = f.read()
        
        self.assertIn("${EMAIL}", hidden_content)
        self.assertIn("${SSN}", hidden_content)
        
        reveal_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            revealed_content = f.read()
        
        self.assertEqual(revealed_content, original_content)
        self.assertFalse(os.path.exists(self.temp_file_path + '.sensitive_backup'))
        self.assertFalse(os.path.exists(self.temp_file_path + '.sensitive_map'))
    
    def test_reveal_without_backup(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Email: ${EMAIL}")
        
        with patch('builtins.print') as mock_print:
            reveal_sensitive_text(self.temp_file_path)
            mock_print.assert_called_with("No backup file found. Cannot reveal sensitive text.")
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content, "Email: ${EMAIL}")
    
    def test_reveal_removes_all_backup_files(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Email: test@example.com")
        
        hide_sensitive_text(self.temp_file_path)
        
        self.assertTrue(os.path.exists(self.temp_file_path + '.sensitive_backup'))
        self.assertTrue(os.path.exists(self.temp_file_path + '.sensitive_map'))
        
        reveal_sensitive_text(self.temp_file_path)
        
        self.assertFalse(os.path.exists(self.temp_file_path + '.sensitive_backup'))
        self.assertFalse(os.path.exists(self.temp_file_path + '.sensitive_map'))

class TestLoadCustomPatterns(unittest.TestCase):
    
    def test_load_patterns_with_string_flags(self):
        patterns_data = [
            {
                'pattern': r'\btest\b',
                'replacement': '${TEST}',
                'flags': 'IGNORECASE'
            },
            {
                'pattern': r'^line',
                'replacement': '${LINE}',
                'flags': 'MULTILINE'
            },
            {
                'pattern': r'both',
                'replacement': '${BOTH}',
                'flags': 'IGNORECASE|MULTILINE'
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(patterns_data, f)
            patterns_file = f.name
        
        try:
            patterns = load_custom_patterns(patterns_file)
            
            self.assertEqual(len(patterns), 3)
            self.assertEqual(patterns[0]['pattern'], r'\btest\b')
            self.assertEqual(patterns[0]['replacement'], '${TEST}')
            self.assertEqual(patterns[0]['flags'], re.IGNORECASE)
            
            self.assertEqual(patterns[1]['pattern'], r'^line')
            self.assertEqual(patterns[1]['replacement'], '${LINE}')
            self.assertEqual(patterns[1]['flags'], re.MULTILINE)
            
            self.assertEqual(patterns[2]['pattern'], r'both')
            self.assertEqual(patterns[2]['replacement'], '${BOTH}')
            self.assertEqual(patterns[2]['flags'], re.IGNORECASE | re.MULTILINE)
        finally:
            os.remove(patterns_file)
    
    def test_load_patterns_with_numeric_flags(self):
        patterns_data = [
            {
                'pattern': r'\btest\b',
                'replacement': '${TEST}',
                'flags': 2
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(patterns_data, f)
            patterns_file = f.name
        
        try:
            patterns = load_custom_patterns(patterns_file)
            
            self.assertEqual(len(patterns), 1)
            self.assertEqual(patterns[0]['flags'], 2)
        finally:
            os.remove(patterns_file)
    
    def test_load_patterns_without_flags(self):
        patterns_data = [
            {
                'pattern': r'\btest\b',
                'replacement': '${TEST}'
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(patterns_data, f)
            patterns_file = f.name
        
        try:
            patterns = load_custom_patterns(patterns_file)
            
            self.assertEqual(len(patterns), 1)
            self.assertEqual(patterns[0]['flags'], 0)
        finally:
            os.remove(patterns_file)
    
    def test_load_patterns_default_replacement(self):
        patterns_data = [
            {
                'pattern': r'\btest\b'
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(patterns_data, f)
            patterns_file = f.name
        
        try:
            patterns = load_custom_patterns(patterns_file)
            
            self.assertEqual(len(patterns), 1)
            self.assertEqual(patterns[0]['replacement'], '${HIDDEN}')
        finally:
            os.remove(patterns_file)

class TestMainFunction(unittest.TestCase):
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.temp_file_path = self.temp_file.name
        self.temp_file.write("Email: test@example.com")
        self.temp_file.close()
    
    def tearDown(self):
        for ext in ['', '.sensitive_backup', '.sensitive_map']:
            file_path = self.temp_file_path + ext
            if os.path.exists(file_path):
                os.remove(file_path)
    
    @patch('sys.argv', ['script.py', 'hide', 'test.txt'])
    @patch('os.path.exists')
    def test_main_hide_action(self, mock_exists):
        mock_exists.return_value = True
        
        with patch('sensitive_text_processor.hide_sensitive_text') as mock_hide:
            with patch('sys.argv', ['script.py', 'hide', self.temp_file_path]):
                main()
                mock_hide.assert_called_once_with(self.temp_file_path, DEFAULT_PATTERNS)
    
    @patch('sys.argv', ['script.py', 'reveal', 'test.txt'])
    @patch('os.path.exists')
    def test_main_reveal_action(self, mock_exists):
        mock_exists.return_value = True
        
        with patch('sensitive_text_processor.reveal_sensitive_text') as mock_reveal:
            with patch('sys.argv', ['script.py', 'reveal', self.temp_file_path]):
                main()
                mock_reveal.assert_called_once_with(self.temp_file_path)
    
    def test_main_file_not_found(self):
        with patch('sys.argv', ['script.py', 'hide', 'nonexistent.txt']):
            with patch('sensitive_text_processor.os.path.exists', return_value=False):
                with patch('sensitive_text_processor.sys.exit', side_effect=SystemExit(1)) as mock_exit:
                    with patch('builtins.print') as mock_print:
                        with self.assertRaises(SystemExit):
                            main()
                        mock_print.assert_called_with("Error: File 'nonexistent.txt' not found")
                        mock_exit.assert_called_with(1)
    
    @patch('sys.argv', ['script.py', 'hide', 'test.txt', '--patterns', 'custom.json'])
    @patch('os.path.exists')
    def test_main_with_custom_patterns(self, mock_exists):
        mock_exists.side_effect = lambda x: x == self.temp_file_path or x == 'custom.json'
        
        custom_patterns = [{'pattern': r'\btest\b', 'replacement': '${TEST}'}]
        
        with patch('sensitive_text_processor.load_custom_patterns', return_value=custom_patterns) as mock_load:
            with patch('sensitive_text_processor.hide_sensitive_text') as mock_hide:
                with patch('sys.argv', ['script.py', 'hide', self.temp_file_path, '--patterns', 'custom.json']):
                    main()
                    mock_load.assert_called_once_with('custom.json')
                    mock_hide.assert_called_once_with(self.temp_file_path, custom_patterns)
    
    @patch('sys.argv', ['script.py', 'hide', 'test.txt', '--patterns', 'nonexistent.json'])
    @patch('os.path.exists')
    def test_main_missing_patterns_file(self, mock_exists):
        mock_exists.side_effect = lambda x: x == self.temp_file_path
        
        with patch('sensitive_text_processor.hide_sensitive_text') as mock_hide:
            with patch('builtins.print') as mock_print:
                with patch('sys.argv', ['script.py', 'hide', self.temp_file_path, '--patterns', 'nonexistent.json']):
                    main()
                    mock_print.assert_called_with("Warning: Patterns file 'nonexistent.json' not found. Using default patterns.")
                    mock_hide.assert_called_once_with(self.temp_file_path, DEFAULT_PATTERNS)

class TestDefaultPatterns(unittest.TestCase):
    
    def test_default_patterns_structure(self):
        self.assertIsInstance(DEFAULT_PATTERNS, list)
        self.assertGreater(len(DEFAULT_PATTERNS), 0)
        
        for pattern in DEFAULT_PATTERNS:
            self.assertIn('pattern', pattern)
            self.assertIn('replacement', pattern)
            self.assertIsInstance(pattern['pattern'], str)
            self.assertIsInstance(pattern['replacement'], str)
            
            if 'flags' in pattern:
                self.assertTrue(isinstance(pattern['flags'], int) or pattern['flags'] == 0)
    
    def test_email_pattern(self):
        email_pattern = next(p for p in DEFAULT_PATTERNS if p['replacement'] == '${EMAIL}')
        regex = re.compile(email_pattern['pattern'])
        
        self.assertIsNotNone(regex.match('test@example.com'))
        self.assertIsNotNone(regex.match('user.name@domain.co.uk'))
        self.assertIsNone(regex.match('not-an-email'))
    
    def test_credit_card_pattern(self):
        cc_pattern = next(p for p in DEFAULT_PATTERNS if p['replacement'] == '${CREDIT_CARD}')
        regex = re.compile(cc_pattern['pattern'])
        
        self.assertIsNotNone(regex.search('1234-5678-9012-3456'))
        self.assertIsNotNone(regex.search('1234 5678 9012 3456'))
        self.assertIsNotNone(regex.search('1234567890123456'))
    
    def test_ssn_pattern(self):
        ssn_pattern = next(p for p in DEFAULT_PATTERNS if p['replacement'] == '${SSN}')
        regex = re.compile(ssn_pattern['pattern'])
        
        self.assertIsNotNone(regex.match('123-45-6789'))
        self.assertIsNone(regex.match('12-345-6789'))
    
    def test_ip_address_pattern(self):
        ip_pattern = next(p for p in DEFAULT_PATTERNS if p['replacement'] == '${IP_ADDRESS}')
        regex = re.compile(ip_pattern['pattern'])
        
        self.assertIsNotNone(regex.match('192.168.1.1'))
        self.assertIsNotNone(regex.match('10.0.0.1'))
        self.assertIsNotNone(regex.match('255.255.255.255'))
        self.assertIsNone(regex.match('256.1.1.1'))
        self.assertIsNone(regex.match('1.1.1.256'))

if __name__ == '__main__':
    unittest.main()