import unittest
import sys
import os
import json
import tempfile
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'standalone-script'))

from sensitive_text_processor import (
    hide_sensitive_text,
    reveal_sensitive_text,
    load_custom_patterns
)

class TestCustomPatternValidation(unittest.TestCase):
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        
        self.pattern_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.pattern_file_path = self.pattern_file.name
        self.pattern_file.close()
    
    def tearDown(self):
        for ext in ['', '.sensitive_backup', '.sensitive_map']:
            file_path = self.temp_file_path + ext
            if os.path.exists(file_path):
                os.remove(file_path)
        
        if os.path.exists(self.pattern_file_path):
            os.remove(self.pattern_file_path)
    
    def test_complex_nested_patterns(self):
        patterns = [
            {
                'pattern': r'(?:Bearer|Token)\s+([A-Za-z0-9\-._~+/]+=*)',
                'replacement': '${AUTH_TOKEN}'
            },
            {
                'pattern': r'mongodb(?:\+srv)?://[^:]+:[^@]+@[^/]+/\w+',
                'replacement': '${MONGO_URI}'
            },
            {
                'pattern': r'postgres://[^:]+:[^@]+@[^:]+:\d+/\w+',
                'replacement': '${POSTGRES_URI}'
            }
        ]
        
        with open(self.pattern_file_path, 'w') as f:
            json.dump(patterns, f)
        
        with open(self.temp_file_path, 'w') as f:
            f.write("""
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
Token abc123def456==
mongodb://user:pass@localhost:27017/mydb
mongodb+srv://admin:secret@cluster.mongodb.net/database
postgres://dbuser:dbpass@localhost:5432/appdb
            """)
        
        loaded_patterns = load_custom_patterns(self.pattern_file_path)
        hide_sensitive_text(self.temp_file_path, loaded_patterns)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("${AUTH_TOKEN}", content)
        self.assertIn("${MONGO_URI}", content)
        self.assertIn("${POSTGRES_URI}", content)
        self.assertNotIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", content)
        self.assertNotIn("mongodb://user:pass", content)
        self.assertNotIn("postgres://dbuser:dbpass", content)
    
    def test_pattern_priority_and_overlap(self):
        patterns = [
            {
                'pattern': r'\b\d{4}-\d{4}-\d{4}-\d{4}\b',
                'replacement': '${CARD_NUMBER}'
            },
            {
                'pattern': r'\b\d{4}-\d{4}\b',
                'replacement': '${SHORT_NUMBER}'
            },
            {
                'pattern': r'\b\d{4}\b',
                'replacement': '${YEAR}'
            }
        ]
        
        with open(self.pattern_file_path, 'w') as f:
            json.dump(patterns, f)
        
        with open(self.temp_file_path, 'w') as f:
            f.write("Numbers: 1234-5678-9012-3456, 1234-5678, 2024")
        
        loaded_patterns = load_custom_patterns(self.pattern_file_path)
        hide_sensitive_text(self.temp_file_path, loaded_patterns)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("${CARD_NUMBER}", content)
        self.assertIn("${SHORT_NUMBER}", content)
        self.assertIn("${YEAR}", content)
    
    def test_invalid_json_handling(self):
        with open(self.pattern_file_path, 'w') as f:
            f.write("{ invalid json }")
        
        with self.assertRaises(json.JSONDecodeError):
            load_custom_patterns(self.pattern_file_path)
    
    def test_missing_required_fields(self):
        patterns = [
            {
                'replacement': '${TEST}'
            }
        ]
        
        with open(self.pattern_file_path, 'w') as f:
            json.dump(patterns, f)
        
        with self.assertRaises(KeyError):
            patterns = load_custom_patterns(self.pattern_file_path)
            for p in patterns:
                re.compile(p['pattern'])
    
    def test_empty_patterns_file(self):
        with open(self.pattern_file_path, 'w') as f:
            json.dump([], f)
        
        patterns = load_custom_patterns(self.pattern_file_path)
        self.assertEqual(len(patterns), 0)
        
        with open(self.temp_file_path, 'w') as f:
            f.write("test@example.com")
        
        hide_sensitive_text(self.temp_file_path, patterns)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content, "test@example.com")
    
    def test_special_regex_characters_in_replacement(self):
        patterns = [
            {
                'pattern': r'secret',
                'replacement': '${$PECIAL_CHAR$}'
            }
        ]
        
        with open(self.pattern_file_path, 'w') as f:
            json.dump(patterns, f)
        
        with open(self.temp_file_path, 'w') as f:
            f.write("This is a secret message")
        
        loaded_patterns = load_custom_patterns(self.pattern_file_path)
        hide_sensitive_text(self.temp_file_path, loaded_patterns)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("${$PECIAL_CHAR$}", content)
        self.assertNotIn("secret", content)
    
    def test_unicode_patterns(self):
        patterns = [
            {
                'pattern': r'密码[:：]\s*\S+',
                'replacement': '${CHINESE_PASSWORD}',
                'flags': 0
            },
            {
                'pattern': r'пароль:\s*\S+',
                'replacement': '${RUSSIAN_PASSWORD}',
                'flags': 'IGNORECASE'
            }
        ]
        
        with open(self.pattern_file_path, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, ensure_ascii=False)
        
        with open(self.temp_file_path, 'w', encoding='utf-8') as f:
            f.write("密码: secret123\nПароль: тайна456\nпароль: секрет789")
        
        loaded_patterns = load_custom_patterns(self.pattern_file_path)
        hide_sensitive_text(self.temp_file_path, loaded_patterns)
        
        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("${CHINESE_PASSWORD}", content)
        self.assertIn("${RUSSIAN_PASSWORD}", content)
        self.assertNotIn("secret123", content)
        self.assertNotIn("тайна456", content)
        self.assertNotIn("секрет789", content)
    
    def test_pattern_with_groups_and_backreferences(self):
        patterns = [
            {
                'pattern': r'(user|admin|root)@(\w+\.com)',
                'replacement': '${ADMIN_EMAIL}'
            },
            {
                'pattern': r'(\w+)@\1\.com',
                'replacement': '${DUPLICATE_DOMAIN}'
            }
        ]
        
        with open(self.pattern_file_path, 'w') as f:
            json.dump(patterns, f)
        
        with open(self.temp_file_path, 'w') as f:
            f.write("Emails: admin@company.com, test@test.com, user@example.com")
        
        loaded_patterns = load_custom_patterns(self.pattern_file_path)
        hide_sensitive_text(self.temp_file_path, loaded_patterns)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("${ADMIN_EMAIL}", content)
        self.assertIn("${DUPLICATE_DOMAIN}", content)
        self.assertNotIn("admin@company.com", content)
        self.assertNotIn("test@test.com", content)
    
    def test_multiline_pattern_with_dotall(self):
        patterns = [
            {
                'pattern': r'BEGIN CERTIFICATE.*?END CERTIFICATE',
                'replacement': '${CERTIFICATE}',
                'flags': 'DOTALL'
            }
        ]
        
        with open(self.pattern_file_path, 'w') as f:
            json.dump(patterns, f)
        
        with open(self.temp_file_path, 'w') as f:
            f.write("""
BEGIN CERTIFICATE
MIIDXTCCAkWgAwIBAgIJAKl
multiple lines
of certificate data
END CERTIFICATE
Some other text
            """)
        
        loaded_patterns = load_custom_patterns(self.pattern_file_path)
        hide_sensitive_text(self.temp_file_path, loaded_patterns)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("${CERTIFICATE}", content)
        self.assertNotIn("MIIDXTCCAkWgAwIBAgIJAKl", content)
        self.assertIn("Some other text", content)
    
    def test_flag_combinations(self):
        patterns = [
            {
                'pattern': r'^secret.*$',
                'replacement': '${SECRET_LINE}',
                'flags': 'IGNORECASE|MULTILINE'
            }
        ]
        
        with open(self.pattern_file_path, 'w') as f:
            json.dump(patterns, f)
        
        with open(self.temp_file_path, 'w') as f:
            f.write("""
Normal line
SECRET data here
Another normal line
Secret: password123
Final line
            """)
        
        loaded_patterns = load_custom_patterns(self.pattern_file_path)
        hide_sensitive_text(self.temp_file_path, loaded_patterns)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content.count("${SECRET_LINE}"), 2)
        self.assertIn("Normal line", content)
        self.assertIn("Another normal line", content)
        self.assertIn("Final line", content)
    
    def test_performance_with_many_patterns(self):
        patterns = []
        for i in range(100):
            patterns.append({
                'pattern': f'pattern_{i:03d}',
                'replacement': f'${{PATTERN_{i:03d}}}'
            })
        
        with open(self.pattern_file_path, 'w') as f:
            json.dump(patterns, f)
        
        content_parts = []
        for i in range(100):
            content_parts.append(f"Text with pattern_{i:03d} included")
        
        with open(self.temp_file_path, 'w') as f:
            f.write('\n'.join(content_parts))
        
        loaded_patterns = load_custom_patterns(self.pattern_file_path)
        
        import time
        start_time = time.time()
        hide_sensitive_text(self.temp_file_path, loaded_patterns)
        process_time = time.time() - start_time
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        for i in range(100):
            self.assertIn(f'${{PATTERN_{i:03d}}}', content)
            self.assertNotIn(f'pattern_{i:03d}', content)
        
        self.assertLess(process_time, 5)
    
    def test_greedy_vs_nongreedy_patterns(self):
        patterns = [
            {
                'pattern': r'start.*end',
                'replacement': '${GREEDY}',
                'flags': 0
            },
            {
                'pattern': r'begin.*?stop',
                'replacement': '${NONGREEDY}',
                'flags': 0
            }
        ]
        
        with open(self.pattern_file_path, 'w') as f:
            json.dump(patterns, f)
        
        with open(self.temp_file_path, 'w') as f:
            f.write("start123end456end and begin123stop456stop")
        
        loaded_patterns = load_custom_patterns(self.pattern_file_path)
        hide_sensitive_text(self.temp_file_path, loaded_patterns)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content.count("${GREEDY}"), 1)
        self.assertEqual(content.count("${NONGREEDY}"), 1)
        self.assertNotIn("start", content)
        self.assertNotIn("begin", content)
        self.assertIn("456stop", content)
    
    def test_word_boundary_patterns(self):
        patterns = [
            {
                'pattern': r'\btest\b',
                'replacement': '${WORD_TEST}'
            },
            {
                'pattern': r'test',
                'replacement': '${ANY_TEST}'
            }
        ]
        
        with open(self.temp_file_path, 'w') as f:
            f.write("test testing contest test123 test")
        
        with open(self.pattern_file_path, 'w') as f:
            json.dump(patterns, f)
        
        loaded_patterns = load_custom_patterns(self.pattern_file_path)
        hide_sensitive_text(self.temp_file_path, loaded_patterns)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        words = content.split()
        self.assertEqual(words[0], "${WORD_TEST}")
        self.assertEqual(words[1], "${ANY_TEST}ing")
        self.assertEqual(words[2], "con${ANY_TEST}")
        self.assertEqual(words[3], "${ANY_TEST}123")
        self.assertEqual(words[4], "${WORD_TEST}")
    
    def test_zero_width_assertions(self):
        patterns = [
            {
                'pattern': r'(?<=password=)\S+',
                'replacement': '${PWD_VALUE}'
            },
            {
                'pattern': r'\S+(?=@example\.com)',
                'replacement': '${USER}'
            }
        ]
        
        with open(self.pattern_file_path, 'w') as f:
            json.dump(patterns, f)
        
        with open(self.temp_file_path, 'w') as f:
            f.write("password=secret123 email: john@example.com")
        
        loaded_patterns = load_custom_patterns(self.pattern_file_path)
        hide_sensitive_text(self.temp_file_path, loaded_patterns)
        
        with open(self.temp_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("password=${PWD_VALUE}", content)
        self.assertIn("${USER}@example.com", content)
        self.assertNotIn("secret123", content)
        self.assertNotIn("john", content)

if __name__ == '__main__':
    unittest.main()