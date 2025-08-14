import unittest
import sys
import os
import time
import tempfile
import random
import string
import statistics
from contextlib import contextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'standalone-script'))

from sensitive_text_processor import (
    hide_sensitive_text,
    reveal_sensitive_text,
    load_custom_patterns,
    DEFAULT_PATTERNS
)

@contextmanager
def measure_time():
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start

class TestPerformanceBenchmarks(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.benchmark_results = []
    
    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def generate_test_content(self, lines, sensitive_ratio=0.3):
        content_lines = []
        sensitive_patterns = [
            lambda: f"user{random.randint(1000, 9999)}@example.com",
            lambda: f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}",
            lambda: f"{random.randint(100, 999)}-45-6789",
            lambda: f"API_KEY_{''.join(random.choices(string.ascii_letters + string.digits, k=20))}",
            lambda: f'password: "{{"".join(random.choices(string.ascii_letters + string.digits, k=8))}}"',
            lambda: f"1234-5678-9012-{random.randint(1000, 9999)}"
        ]
        
        for i in range(lines):
            if random.random() < sensitive_ratio:
                pattern_func = random.choice(sensitive_patterns)
                line = f"Line {i}: {pattern_func()} - some text"
            else:
                line = f"Line {i}: {''.join(random.choices(string.ascii_letters + string.digits + ' ', k=50))}"
            content_lines.append(line)
        
        return '\n'.join(content_lines)
    
    def benchmark_operation(self, operation, content, iterations=5):
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', dir=self.temp_dir)
        temp_file.write(content)
        temp_file.close()
        
        times = []
        try:
            for _ in range(iterations):
                with open(temp_file.name, 'w') as f:
                    f.write(content)
                
                with measure_time() as elapsed:
                    operation(temp_file.name)
                    times.append(elapsed())
                
                for ext in ['.sensitive_backup', '.sensitive_map']:
                    backup_file = temp_file.name + ext
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
            
            return {
                'mean': statistics.mean(times),
                'median': statistics.median(times),
                'stdev': statistics.stdev(times) if len(times) > 1 else 0,
                'min': min(times),
                'max': max(times)
            }
        finally:
            os.remove(temp_file.name)
    
    def test_baseline_performance_small_file(self):
        content = self.generate_test_content(100, sensitive_ratio=0.3)
        
        hide_stats = self.benchmark_operation(hide_sensitive_text, content)
        
        self.assertLess(hide_stats['mean'], 0.1)
        self.assertLess(hide_stats['max'], 0.2)
        
        print(f"\nSmall file (100 lines) hide performance:")
        print(f"  Mean: {hide_stats['mean']*1000:.2f}ms")
        print(f"  Median: {hide_stats['median']*1000:.2f}ms")
        print(f"  StdDev: {hide_stats['stdev']*1000:.2f}ms")
    
    def test_baseline_performance_medium_file(self):
        content = self.generate_test_content(1000, sensitive_ratio=0.3)
        
        hide_stats = self.benchmark_operation(hide_sensitive_text, content)
        
        self.assertLess(hide_stats['mean'], 0.5)
        self.assertLess(hide_stats['max'], 1.0)
        
        print(f"\nMedium file (1000 lines) hide performance:")
        print(f"  Mean: {hide_stats['mean']*1000:.2f}ms")
        print(f"  Median: {hide_stats['median']*1000:.2f}ms")
        print(f"  StdDev: {hide_stats['stdev']*1000:.2f}ms")
    
    def test_baseline_performance_large_file(self):
        content = self.generate_test_content(10000, sensitive_ratio=0.3)
        
        hide_stats = self.benchmark_operation(hide_sensitive_text, content, iterations=3)
        
        self.assertLess(hide_stats['mean'], 5.0)
        self.assertLess(hide_stats['max'], 10.0)
        
        print(f"\nLarge file (10000 lines) hide performance:")
        print(f"  Mean: {hide_stats['mean']:.2f}s")
        print(f"  Median: {hide_stats['median']:.2f}s")
        print(f"  StdDev: {hide_stats['stdev']:.2f}s")
    
    def test_performance_scaling_linearity(self):
        sizes = [100, 500, 1000, 2000, 4000]
        results = []
        
        for size in sizes:
            content = self.generate_test_content(size, sensitive_ratio=0.3)
            stats = self.benchmark_operation(hide_sensitive_text, content, iterations=3)
            results.append((size, stats['mean']))
            
            print(f"\n{size} lines: {stats['mean']*1000:.2f}ms")
        
        for i in range(1, len(results)):
            size_ratio = results[i][0] / results[i-1][0]
            time_ratio = results[i][1] / results[i-1][1]
            
            self.assertLess(time_ratio, size_ratio * 2.5)
    
    def test_performance_with_varying_sensitive_density(self):
        lines = 1000
        densities = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        print("\nPerformance vs sensitive data density:")
        for density in densities:
            content = self.generate_test_content(lines, sensitive_ratio=density)
            stats = self.benchmark_operation(hide_sensitive_text, content, iterations=3)
            
            print(f"  {int(density*100)}% sensitive: {stats['mean']*1000:.2f}ms")
            
            self.assertLess(stats['mean'], 2.0)
    
    def test_pattern_complexity_impact(self):
        simple_patterns = [
            {'pattern': r'test', 'replacement': '${TEST}'}
        ]
        
        complex_patterns = [
            {'pattern': r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)', 
             'replacement': '${IP}'},
            {'pattern': r'\b[A-Za-z0-9+/]{20,}={0,2}\b', 
             'replacement': '${BASE64}'},
            {'pattern': r'(?:mongodb(?:\+srv)?|postgres|mysql)://[^:]+:[^@]+@[^/]+/\w+', 
             'replacement': '${DB_URI}'}
        ]
        
        content = self.generate_test_content(1000, sensitive_ratio=0.3)
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', dir=self.temp_dir)
        temp_file.write(content)
        temp_file.close()
        
        try:
            with measure_time() as elapsed:
                hide_sensitive_text(temp_file.name, simple_patterns)
                simple_time = elapsed()
            
            for ext in ['.sensitive_backup', '.sensitive_map']:
                backup_file = temp_file.name + ext
                if os.path.exists(backup_file):
                    os.remove(backup_file)
            
            with open(temp_file.name, 'w') as f:
                f.write(content)
            
            with measure_time() as elapsed:
                hide_sensitive_text(temp_file.name, complex_patterns)
                complex_time = elapsed()
            
            print(f"\nPattern complexity impact:")
            print(f"  Simple patterns: {simple_time*1000:.2f}ms")
            print(f"  Complex patterns: {complex_time*1000:.2f}ms")
            print(f"  Ratio: {complex_time/simple_time:.2f}x")
            
            self.assertLess(complex_time / simple_time, 250)
        finally:
            os.remove(temp_file.name)
            for ext in ['.sensitive_backup', '.sensitive_map']:
                backup_file = temp_file.name + ext
                if os.path.exists(backup_file):
                    os.remove(backup_file)
    
    def test_reveal_performance(self):
        content = self.generate_test_content(1000, sensitive_ratio=0.5)
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', dir=self.temp_dir)
        temp_file.write(content)
        temp_file.close()
        
        try:
            hide_sensitive_text(temp_file.name)
            
            reveal_times = []
            for _ in range(5):
                with measure_time() as elapsed:
                    reveal_sensitive_text(temp_file.name)
                    reveal_times.append(elapsed())
                
                hide_sensitive_text(temp_file.name)
            
            mean_reveal = statistics.mean(reveal_times)
            
            print(f"\nReveal performance (1000 lines):")
            print(f"  Mean: {mean_reveal*1000:.2f}ms")
            
            self.assertLess(mean_reveal, 0.5)
        finally:
            os.remove(temp_file.name)
            for ext in ['.sensitive_backup', '.sensitive_map']:
                backup_file = temp_file.name + ext
                if os.path.exists(backup_file):
                    os.remove(backup_file)
    
    def test_memory_usage_trend(self):
        import tracemalloc
        
        sizes = [100, 1000, 5000, 10000]
        memory_usage = []
        
        print("\nMemory usage trend:")
        for size in sizes:
            content = self.generate_test_content(size, sensitive_ratio=0.3)
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', dir=self.temp_dir)
            temp_file.write(content)
            temp_file.close()
            
            try:
                tracemalloc.start()
                hide_sensitive_text(temp_file.name)
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                
                peak_mb = peak / (1024 * 1024)
                memory_usage.append((size, peak_mb))
                
                print(f"  {size} lines: {peak_mb:.2f}MB")
                
                self.assertLess(peak_mb, size * 0.01)
            finally:
                os.remove(temp_file.name)
                for ext in ['.sensitive_backup', '.sensitive_map']:
                    backup_file = temp_file.name + ext
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
        
        for i in range(1, len(memory_usage)):
            size_ratio = memory_usage[i][0] / memory_usage[i-1][0]
            memory_ratio = memory_usage[i][1] / memory_usage[i-1][1]
            
            self.assertLess(memory_ratio, size_ratio * 1.5)
    
    def test_worst_case_performance(self):
        worst_case_content = ""
        for i in range(1000):
            worst_case_content += f"test{i}@example.com " * 10 + "\n"
            worst_case_content += f"192.168.{i % 256}.{(i * 7) % 256} " * 10 + "\n"
            worst_case_content += f"{(i % 900) + 100:03d}-45-6789 " * 10 + "\n"
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', dir=self.temp_dir)
        temp_file.write(worst_case_content)
        temp_file.close()
        
        try:
            with measure_time() as elapsed:
                hide_sensitive_text(temp_file.name)
                worst_time = elapsed()
            
            print(f"\nWorst case performance (30000 sensitive items):")
            print(f"  Time: {worst_time:.2f}s")
            
            self.assertLess(worst_time, 30)
        finally:
            os.remove(temp_file.name)
            for ext in ['.sensitive_backup', '.sensitive_map']:
                backup_file = temp_file.name + ext
                if os.path.exists(backup_file):
                    os.remove(backup_file)
    
    def test_pattern_caching_benefit(self):
        content = self.generate_test_content(1000, sensitive_ratio=0.3)
        
        first_run_times = []
        subsequent_run_times = []
        
        for i in range(10):
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', dir=self.temp_dir)
            temp_file.write(content)
            temp_file.close()
            
            try:
                with measure_time() as elapsed:
                    hide_sensitive_text(temp_file.name, DEFAULT_PATTERNS)
                    time_taken = elapsed()
                
                if i == 0:
                    first_run_times.append(time_taken)
                else:
                    subsequent_run_times.append(time_taken)
            finally:
                os.remove(temp_file.name)
                for ext in ['.sensitive_backup', '.sensitive_map']:
                    backup_file = temp_file.name + ext
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
        
        if subsequent_run_times:
            mean_subsequent = statistics.mean(subsequent_run_times)
            print(f"\nPattern caching benefit:")
            print(f"  First run: {first_run_times[0]*1000:.2f}ms")
            print(f"  Subsequent mean: {mean_subsequent*1000:.2f}ms")
    
    def test_parallel_file_processing_overhead(self):
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        num_files = 10
        content = self.generate_test_content(500, sensitive_ratio=0.3)
        
        files = []
        for i in range(num_files):
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', dir=self.temp_dir)
            temp_file.write(content)
            temp_file.close()
            files.append(temp_file.name)
        
        try:
            with measure_time() as elapsed:
                for file_path in files:
                    hide_sensitive_text(file_path)
                sequential_time = elapsed()
            
            for file_path in files:
                for ext in ['.sensitive_backup', '.sensitive_map']:
                    backup_file = file_path + ext
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                with open(file_path, 'w') as f:
                    f.write(content)
            
            with measure_time() as elapsed:
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = [executor.submit(hide_sensitive_text, f) for f in files]
                    for future in as_completed(futures):
                        future.result()
                parallel_time = elapsed()
            
            speedup = sequential_time / parallel_time
            
            print(f"\nParallel processing ({num_files} files):")
            print(f"  Sequential: {sequential_time:.2f}s")
            print(f"  Parallel (4 workers): {parallel_time:.2f}s")
            print(f"  Speedup: {speedup:.2f}x")
            
            self.assertGreater(speedup, 0.8)
        finally:
            for file_path in files:
                os.remove(file_path)
                for ext in ['.sensitive_backup', '.sensitive_map']:
                    backup_file = file_path + ext
                    if os.path.exists(backup_file):
                        os.remove(backup_file)

if __name__ == '__main__':
    unittest.main(verbosity=2)