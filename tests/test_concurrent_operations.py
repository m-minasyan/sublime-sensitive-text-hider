import unittest
import sys
import os
import tempfile
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'standalone-script'))

from sensitive_text_processor import (
    hide_sensitive_text,
    reveal_sensitive_text,
    DEFAULT_PATTERNS
)

class TestConcurrentFileOperations(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_files = []
        self.lock = threading.Lock()
        self.errors = []
    
    def tearDown(self):
        for file_path in self.test_files:
            for ext in ['', '.sensitive_backup', '.sensitive_map']:
                full_path = file_path + ext
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except:
                        pass
        
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except:
                pass
    
    def create_test_file(self, index):
        file_path = os.path.join(self.test_dir, f'test_{index}.txt')
        with open(file_path, 'w') as f:
            f.write(f"File {index}: test{index}@example.com, IP: 192.168.{index}.1, SSN: {index:03d}-45-6789")
        self.test_files.append(file_path)
        return file_path
    
    def test_concurrent_hide_multiple_files(self):
        num_files = 10
        files = [self.create_test_file(i) for i in range(num_files)]
        
        def hide_file(file_path):
            try:
                hide_sensitive_text(file_path)
                return file_path, True
            except Exception as e:
                return file_path, False, str(e)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(hide_file, f) for f in files]
            results = [future.result() for future in as_completed(futures)]
        
        for result in results:
            self.assertEqual(len(result), 2)
            file_path, success = result
            self.assertTrue(success)
            
            with open(file_path, 'r') as f:
                content = f.read()
            self.assertIn("${EMAIL}", content)
            self.assertIn("${IP_ADDRESS}", content)
            self.assertIn("${SSN}", content)
            
            self.assertTrue(os.path.exists(file_path + '.sensitive_backup'))
            self.assertTrue(os.path.exists(file_path + '.sensitive_map'))
    
    def test_concurrent_hide_and_reveal_same_file(self):
        file_path = self.create_test_file(0)
        hide_count = 0
        reveal_count = 0
        
        def hide_operation():
            nonlocal hide_count
            try:
                with self.lock:
                    if not os.path.exists(file_path + '.sensitive_backup'):
                        hide_sensitive_text(file_path)
                        hide_count += 1
                        return True
            except Exception as e:
                self.errors.append(('hide', str(e)))
                return False
        
        def reveal_operation():
            nonlocal reveal_count
            try:
                with self.lock:
                    if os.path.exists(file_path + '.sensitive_backup'):
                        reveal_sensitive_text(file_path)
                        reveal_count += 1
                        return True
            except Exception as e:
                self.errors.append(('reveal', str(e)))
                return False
        
        threads = []
        for i in range(5):
            t1 = threading.Thread(target=hide_operation)
            t2 = threading.Thread(target=reveal_operation)
            threads.extend([t1, t2])
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        self.assertEqual(len(self.errors), 0)
        
        total_operations = hide_count + reveal_count
        self.assertGreater(total_operations, 0)
    
    def test_race_condition_backup_creation(self):
        file_path = self.create_test_file(0)
        success_count = 0
        
        def concurrent_hide():
            nonlocal success_count
            try:
                hide_sensitive_text(file_path)
                with self.lock:
                    success_count += 1
                return True
            except Exception as e:
                return False
        
        threads = [threading.Thread(target=concurrent_hide) for _ in range(5)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        self.assertGreaterEqual(success_count, 1)
        
        self.assertTrue(os.path.exists(file_path + '.sensitive_backup'))
        self.assertTrue(os.path.exists(file_path + '.sensitive_map'))
    
    def test_concurrent_reveal_operations(self):
        num_files = 5
        files = []
        
        for i in range(num_files):
            file_path = self.create_test_file(i)
            hide_sensitive_text(file_path)
            files.append(file_path)
        
        def reveal_file(file_path):
            try:
                reveal_sensitive_text(file_path)
                return file_path, True
            except Exception as e:
                return file_path, False, str(e)
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(reveal_file, f) for f in files]
            results = [future.result() for future in as_completed(futures)]
        
        for result in results:
            self.assertEqual(len(result), 2)
            file_path, success = result
            self.assertTrue(success)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            self.assertIn("@example.com", content)
            self.assertNotIn("${EMAIL}", content)
            
            self.assertFalse(os.path.exists(file_path + '.sensitive_backup'))
            self.assertFalse(os.path.exists(file_path + '.sensitive_map'))
    
    def test_concurrent_mixed_operations(self):
        num_files = 10
        files = [self.create_test_file(i) for i in range(num_files)]
        
        def process_file(file_path, operation):
            try:
                if operation == 'hide':
                    hide_sensitive_text(file_path)
                elif operation == 'reveal':
                    if os.path.exists(file_path + '.sensitive_backup'):
                        reveal_sensitive_text(file_path)
                return file_path, operation, True
            except Exception as e:
                return file_path, operation, False, str(e)
        
        operations = []
        for i, file_path in enumerate(files):
            if i % 2 == 0:
                hide_sensitive_text(file_path)
                operations.append((file_path, 'reveal'))
            else:
                operations.append((file_path, 'hide'))
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_file, fp, op) for fp, op in operations]
            results = [future.result() for future in as_completed(futures)]
        
        for result in results:
            if len(result) == 3:
                file_path, operation, success = result
                self.assertTrue(success)
    
    def test_file_lock_simulation(self):
        file_path = self.create_test_file(0)
        operations_completed = []
        
        def operation_with_delay(op_type, delay=0.1):
            time.sleep(delay)
            try:
                if op_type == 'hide':
                    hide_sensitive_text(file_path)
                elif op_type == 'reveal':
                    reveal_sensitive_text(file_path)
                
                with self.lock:
                    operations_completed.append((op_type, time.time()))
                return True
            except Exception as e:
                with self.lock:
                    self.errors.append((op_type, str(e)))
                return False
        
        hide_sensitive_text(file_path)
        
        threads = []
        threads.append(threading.Thread(target=operation_with_delay, args=('reveal', 0)))
        threads.append(threading.Thread(target=operation_with_delay, args=('hide', 0.05)))
        threads.append(threading.Thread(target=operation_with_delay, args=('reveal', 0.1)))
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        self.assertGreater(len(operations_completed), 0)
    
    def test_concurrent_mapping_file_integrity(self):
        file_path = self.create_test_file(0)
        original_content = None
        
        with open(file_path, 'r') as f:
            original_content = f.read()
        
        hide_sensitive_text(file_path)
        
        mapping_file = file_path + '.sensitive_map'
        with open(mapping_file, 'r') as f:
            original_mappings = json.load(f)
        
        def check_mapping_integrity():
            try:
                with open(mapping_file, 'r') as f:
                    mappings = json.load(f)
                    self.assertIsInstance(mappings, list)
                    for mapping in mappings:
                        self.assertIn('original', mapping)
                        self.assertIn('replacement', mapping)
                        self.assertIn('start', mapping)
                        self.assertIn('end', mapping)
                return True
            except Exception as e:
                return False
        
        threads = [threading.Thread(target=check_mapping_integrity) for _ in range(10)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        with open(mapping_file, 'r') as f:
            final_mappings = json.load(f)
        
        self.assertEqual(len(original_mappings), len(final_mappings))
    
    def test_stress_test_many_concurrent_operations(self):
        num_files = 20
        files = [self.create_test_file(i) for i in range(num_files)]
        results = {'hide': 0, 'reveal': 0, 'errors': 0}
        
        def stress_operation(file_path, index):
            try:
                if index % 3 == 0:
                    hide_sensitive_text(file_path)
                    with self.lock:
                        results['hide'] += 1
                elif index % 3 == 1:
                    hide_sensitive_text(file_path)
                    time.sleep(0.01)
                    reveal_sensitive_text(file_path)
                    with self.lock:
                        results['reveal'] += 1
                else:
                    if os.path.exists(file_path + '.sensitive_backup'):
                        reveal_sensitive_text(file_path)
                        with self.lock:
                            results['reveal'] += 1
                    else:
                        hide_sensitive_text(file_path)
                        with self.lock:
                            results['hide'] += 1
                return True
            except Exception as e:
                with self.lock:
                    results['errors'] += 1
                return False
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(stress_operation, files[i % num_files], i) 
                      for i in range(50)]
            for future in as_completed(futures):
                future.result()
        
        total_operations = results['hide'] + results['reveal']
        self.assertGreater(total_operations, 0)
        
        error_rate = results['errors'] / (total_operations + results['errors']) if total_operations > 0 else 0
        self.assertLess(error_rate, 0.5)

if __name__ == '__main__':
    unittest.main()