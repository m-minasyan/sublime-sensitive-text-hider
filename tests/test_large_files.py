import unittest
import sys
import os
import tempfile
import time
import random
import string

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'standalone-script'))

from sensitive_text_processor import (
    hide_sensitive_text,
    reveal_sensitive_text,
    DEFAULT_PATTERNS
)

class TestLargeFileHandling(unittest.TestCase):
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
    
    def tearDown(self):
        for ext in ['', '.sensitive_backup', '.sensitive_map']:
            file_path = self.temp_file_path + ext
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def generate_large_content(self, size_mb, sensitive_density=0.01):
        chars_per_mb = 1024 * 1024
        total_chars = size_mb * chars_per_mb
        
        content_parts = []
        chars_written = 0
        
        sensitive_patterns = [
            "test{}@example.com",
            "192.168.{}.{}",
            "{}-45-6789",
            "API_KEY_{}",
            "password: \"{}\"",
            "1234-5678-9012-{}"
        ]
        
        while chars_written < total_chars:
            if random.random() < sensitive_density:
                pattern = random.choice(sensitive_patterns)
                if pattern.startswith("test"):
                    sensitive_text = pattern.format(
                        ''.join(random.choices(string.digits, k=3))
                    )
                elif pattern.startswith("192.168"):
                    sensitive_text = pattern.format(
                        random.randint(0, 255),
                        random.randint(0, 255)
                    )
                elif pattern.endswith("-45-6789"):
                    sensitive_text = pattern.format(
                        ''.join(random.choices(string.digits, k=3))
                    )
                elif "API_KEY" in pattern:
                    sensitive_text = pattern.format(
                        ''.join(random.choices(string.ascii_letters + string.digits, k=20))
                    )
                elif "password" in pattern:
                    sensitive_text = pattern.format(
                        ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                    )
                elif "1234-5678" in pattern:
                    sensitive_text = pattern.format(
                        ''.join(random.choices(string.digits, k=4))
                    )
                else:
                    sensitive_text = pattern
                content_parts.append(sensitive_text)
                chars_written += len(sensitive_text)
            else:
                remaining = total_chars - chars_written
                if remaining <= 0:
                    break
                normal_text = ''.join(random.choices(
                    string.ascii_letters + string.digits + ' \n', 
                    k=min(100, int(remaining))
                ))
                content_parts.append(normal_text)
                chars_written += len(normal_text)
        
        return ''.join(content_parts)[:int(total_chars)]
    
    def test_small_large_file_1mb(self):
        content = self.generate_large_content(1, sensitive_density=0.001)
        
        with open(self.temp_file_path, 'w') as f:
            f.write(content)
        
        start_time = time.time()
        hide_sensitive_text(self.temp_file_path)
        hide_time = time.time() - start_time
        
        self.assertTrue(os.path.exists(self.temp_file_path + '.sensitive_backup'))
        self.assertTrue(os.path.exists(self.temp_file_path + '.sensitive_map'))
        
        with open(self.temp_file_path, 'r') as f:
            hidden_content = f.read()
        
        self.assertIn("${", hidden_content)
        
        start_time = time.time()
        reveal_sensitive_text(self.temp_file_path)
        reveal_time = time.time() - start_time
        
        with open(self.temp_file_path, 'r') as f:
            revealed_content = f.read()
        
        self.assertEqual(len(revealed_content), len(content))
        
        self.assertLess(hide_time, 5)
        self.assertLess(reveal_time, 5)
    
    def test_medium_large_file_5mb(self):
        content = self.generate_large_content(5, sensitive_density=0.0005)
        
        with open(self.temp_file_path, 'w') as f:
            f.write(content)
        
        file_size_mb = os.path.getsize(self.temp_file_path) / (1024 * 1024)
        self.assertGreater(file_size_mb, 4.5)
        
        start_time = time.time()
        hide_sensitive_text(self.temp_file_path)
        hide_time = time.time() - start_time
        
        with open(self.temp_file_path, 'r') as f:
            hidden_content = f.read()
        
        sensitive_count = hidden_content.count("${EMAIL}")
        sensitive_count += hidden_content.count("${IP_ADDRESS}")
        sensitive_count += hidden_content.count("${SSN}")
        sensitive_count += hidden_content.count("${API_KEY}")
        sensitive_count += hidden_content.count("${PASSWORD}")
        sensitive_count += hidden_content.count("${CREDIT_CARD}")
        
        self.assertGreater(sensitive_count, 0)
        
        reveal_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            revealed_content = f.read()
        
        self.assertEqual(len(revealed_content), len(content))
        
        self.assertLess(hide_time, 10)
    
    def test_many_sensitive_items(self):
        lines = []
        for i in range(10000):
            if i % 4 == 0:
                lines.append(f"Email {i}: user{i}@example.com")
            elif i % 4 == 1:
                lines.append(f"IP {i}: 10.0.{i % 256}.{(i * 7) % 256}")
            elif i % 4 == 2:
                lines.append(f"SSN {i}: {(i % 900) + 100:03d}-45-6789")
            else:
                lines.append(f"Normal text line {i} with no sensitive data")
        
        content = '\n'.join(lines)
        
        with open(self.temp_file_path, 'w') as f:
            f.write(content)
        
        start_time = time.time()
        hide_sensitive_text(self.temp_file_path)
        process_time = time.time() - start_time
        
        with open(self.temp_file_path + '.sensitive_map', 'r') as f:
            import json
            mappings = json.load(f)
        
        self.assertGreater(len(mappings), 7000)
        
        with open(self.temp_file_path, 'r') as f:
            hidden_content = f.read()
        
        self.assertNotIn("@example.com", hidden_content)
        self.assertNotIn("10.0.", hidden_content)
        self.assertNotIn("-45-6789", hidden_content)
        
        reveal_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            revealed_content = f.read()
        
        self.assertEqual(revealed_content, content)
        
        self.assertLess(process_time, 15)
    
    def test_file_with_no_newlines(self):
        content = ' '.join([f"test{i}@example.com" for i in range(1000)])
        content += ' ' + ' '.join([f"192.168.{i % 256}.1" for i in range(1000)])
        
        with open(self.temp_file_path, 'w') as f:
            f.write(content)
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            hidden_content = f.read()
        
        self.assertEqual(hidden_content.count("${EMAIL}"), 1000)
        self.assertEqual(hidden_content.count("${IP_ADDRESS}"), 1000)
        
        reveal_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            revealed_content = f.read()
        
        self.assertEqual(revealed_content, content)
    
    def test_file_with_long_lines(self):
        lines = []
        for i in range(100):
            long_line = f"Line {i}: "
            for j in range(100):
                long_line += f"test{i}_{j}@example.com "
            lines.append(long_line)
        
        content = '\n'.join(lines)
        
        with open(self.temp_file_path, 'w') as f:
            f.write(content)
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            hidden_content = f.read()
        
        email_count = hidden_content.count("${EMAIL}")
        self.assertEqual(email_count, 10000)
        
        reveal_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            revealed_content = f.read()
        
        self.assertEqual(revealed_content, content)
    
    def test_memory_efficiency(self):
        content = self.generate_large_content(2, sensitive_density=0.001)
        
        with open(self.temp_file_path, 'w') as f:
            f.write(content)
        
        import tracemalloc
        tracemalloc.start()
        
        hide_sensitive_text(self.temp_file_path)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_mb = peak / (1024 * 1024)
        self.assertLess(peak_mb, 100)
        
        reveal_sensitive_text(self.temp_file_path)
    
    def test_incremental_file_growth(self):
        sizes = [0.1, 0.5, 1, 2]
        times = []
        
        for size_mb in sizes:
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
            temp_path = temp_file.name
            temp_file.close()
            
            try:
                content = self.generate_large_content(size_mb, sensitive_density=0.001)
                
                with open(temp_path, 'w') as f:
                    f.write(content)
                
                start_time = time.time()
                hide_sensitive_text(temp_path)
                process_time = time.time() - start_time
                times.append((size_mb, process_time))
                
                reveal_sensitive_text(temp_path)
            finally:
                for ext in ['', '.sensitive_backup', '.sensitive_map']:
                    file_path = temp_path + ext
                    if os.path.exists(file_path):
                        os.remove(file_path)
        
        for i in range(1, len(times)):
            size_ratio = times[i][0] / times[i-1][0]
            time_ratio = times[i][1] / times[i-1][1]
            
            self.assertLess(time_ratio, size_ratio * 2)
    
    def test_binary_safe_handling(self):
        content = "Before binary\n"
        content += "Email: test@example.com\n"
        content += "\x00\x01\x02\x03\x04\x05"
        content += "\nAfter binary\n"
        content += "IP: 192.168.1.1\n"
        
        with open(self.temp_file_path, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(content)
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            hidden_content = f.read()
        
        self.assertIn("${EMAIL}", hidden_content)
        self.assertIn("${IP_ADDRESS}", hidden_content)
        
        reveal_sensitive_text(self.temp_file_path)
    
    def test_sparse_sensitive_data(self):
        content_parts = []
        for i in range(1000):
            content_parts.append(''.join(random.choices(string.ascii_letters + ' \n', k=1000)))
            if i % 100 == 0:
                content_parts.append(f"RARE_EMAIL_{i}@example.com")
        
        content = ''.join(content_parts)
        
        with open(self.temp_file_path, 'w') as f:
            f.write(content)
        
        hide_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            hidden_content = f.read()
        
        email_count = hidden_content.count("${EMAIL}")
        self.assertEqual(email_count, 10)
        
        reveal_sensitive_text(self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            revealed_content = f.read()
        
        self.assertEqual(revealed_content, content)

if __name__ == '__main__':
    unittest.main()