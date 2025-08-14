import unittest
import sys
import os
import json
import tempfile
from unittest.mock import Mock, MagicMock, patch, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sublime-plugin'))

class MockSublimeRegion:
    def __init__(self, start, end):
        self.a = start
        self.b = end

class MockSublimeView:
    def __init__(self):
        self.id_value = 12345
        self._content = ""
        self._file_name = None
        self.replacements = []
        
    def id(self):
        return self.id_value
    
    def file_name(self):
        return self._file_name
    
    def size(self):
        return len(self._content)
    
    def substr(self, region):
        return self._content[region.a:region.b]
    
    def replace(self, edit, region, text):
        self.replacements.append((region.a, region.b, text))
        self._content = self._content[:region.a] + text + self._content[region.b:]
    
    def run_command(self, command_name):
        pass

class MockSublimeSettings:
    def __init__(self):
        self.settings = {}
    
    def get(self, key, default=None):
        return self.settings.get(key, default)
    
    def set(self, key, value):
        self.settings[key] = value

class MockTextCommand:
    def __init__(self, view):
        self.view = view

class MockWindowCommand:
    def __init__(self, window):
        self.window = window

class MockEventListener:
    pass

sys.modules['sublime'] = MagicMock()
sys.modules['sublime_plugin'] = MagicMock()

import sublime
import sublime_plugin

global_settings = MockSublimeSettings()

sublime.Region = MockSublimeRegion
sublime.load_settings = MagicMock(return_value=global_settings)
sublime.save_settings = MagicMock()
sublime.status_message = MagicMock()

sublime_plugin.TextCommand = MockTextCommand
sublime_plugin.WindowCommand = MockWindowCommand
sublime_plugin.EventListener = MockEventListener

import hide_sensitive_text
sensitive_mappings = hide_sensitive_text.sensitive_mappings

class TestHideSensitiveTextCommand(unittest.TestCase):
    
    def setUp(self):
        self.view = MockSublimeView()
        sensitive_mappings.clear()
        global_settings.settings.clear()
        sublime.status_message.reset_mock()
    
    def test_hide_email_address(self):
        self.view._content = "Contact us at john.doe@example.com for more info"
        edit = MagicMock()
        
        cmd = hide_sensitive_text.HideSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.assertIn("${EMAIL}", self.view._content)
        self.assertNotIn("john.doe@example.com", self.view._content)
        sublime.status_message.assert_called_with("Hidden 1 sensitive text occurrences")
    
    def test_hide_credit_card_number(self):
        self.view._content = "Payment with card 1234-5678-9012-3456"
        edit = MagicMock()
        
        cmd = hide_sensitive_text.HideSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.assertIn("${CREDIT_CARD}", self.view._content)
        self.assertNotIn("1234-5678-9012-3456", self.view._content)
    
    def test_hide_ssn(self):
        self.view._content = "SSN: 123-45-6789"
        edit = MagicMock()
        
        cmd = hide_sensitive_text.HideSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.assertIn("${SSN}", self.view._content)
        self.assertNotIn("123-45-6789", self.view._content)
    
    def test_hide_ip_address(self):
        self.view._content = "Server IP: 192.168.1.1"
        edit = MagicMock()
        
        cmd = hide_sensitive_text.HideSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.assertIn("${IP_ADDRESS}", self.view._content)
        self.assertNotIn("192.168.1.1", self.view._content)
    
    def test_hide_api_key(self):
        self.view._content = "Use apikey_abcdef1234567890ghijklmnop"
        edit = MagicMock()
        
        cmd = hide_sensitive_text.HideSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.assertIn("${API_KEY}", self.view._content)
        self.assertNotIn("apikey_abcdef1234567890ghijklmnop", self.view._content)
    
    def test_hide_multiple_patterns(self):
        self.view._content = "Email: test@example.com, IP: 10.0.0.1, SSN: 123-45-6789"
        edit = MagicMock()
        
        cmd = hide_sensitive_text.HideSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.assertIn("${EMAIL}", self.view._content)
        self.assertIn("${IP_ADDRESS}", self.view._content)
        self.assertIn("${SSN}", self.view._content)
        self.assertNotIn("test@example.com", self.view._content)
        self.assertNotIn("10.0.0.1", self.view._content)
        self.assertNotIn("123-45-6789", self.view._content)
        sublime.status_message.assert_called_with("Hidden 3 sensitive text occurrences")
    
    def test_no_sensitive_text_found(self):
        self.view._content = "This is just normal text"
        edit = MagicMock()
        
        cmd = hide_sensitive_text.HideSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.assertEqual("This is just normal text", self.view._content)
        sublime.status_message.assert_called_with("No sensitive text found to hide")
    
    @patch('builtins.open', new_callable=mock_open)
    def test_save_backup_for_file(self, mock_file):
        self.view._file_name = "/path/to/file.txt"
        self.view._content = "Email: test@example.com"
        edit = MagicMock()
        
        cmd = hide_sensitive_text.HideSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        mock_file.assert_any_call("/path/to/file.txt.sensitive_backup", 'w', encoding='utf-8')
        mock_file.assert_any_call("/path/to/file.txt.sensitive_map", 'w', encoding='utf-8')
    
    def test_in_memory_backup_for_unsaved_file(self):
        self.view._content = "Email: test@example.com"
        edit = MagicMock()
        
        cmd = hide_sensitive_text.HideSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.assertIn(self.view.id_value, sensitive_mappings)
        self.assertEqual(sensitive_mappings[self.view.id_value]['original'], "Email: test@example.com")
        self.assertIn('replacements', sensitive_mappings[self.view.id_value])

class TestRevealSensitiveTextCommand(unittest.TestCase):
    
    def setUp(self):
        self.view = MockSublimeView()
        sensitive_mappings.clear()
        global_settings.settings.clear()
        sublime.status_message.reset_mock()
    
    def test_reveal_from_memory(self):
        original = "Email: test@example.com"
        self.view._content = "Email: ${EMAIL}"
        sensitive_mappings[self.view.id_value] = {'original': original}
        edit = MagicMock()
        
        cmd = hide_sensitive_text.RevealSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.assertEqual(self.view._content, original)
        self.assertNotIn(self.view.id_value, sensitive_mappings)
        sublime.status_message.assert_called_with("Sensitive text revealed")
    
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', mock_open(read_data="Email: test@example.com"))
    @patch('os.remove')
    def test_reveal_from_file(self, mock_remove, mock_exists):
        self.view._file_name = "/path/to/file.txt"
        self.view._content = "Email: ${EMAIL}"
        edit = MagicMock()
        
        cmd = hide_sensitive_text.RevealSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.assertEqual(self.view._content, "Email: test@example.com")
        mock_remove.assert_any_call("/path/to/file.txt.sensitive_backup")
        sublime.status_message.assert_called_with("Sensitive text revealed")
    
    def test_no_backup_found(self):
        self.view._content = "Email: ${EMAIL}"
        edit = MagicMock()
        
        cmd = hide_sensitive_text.RevealSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.assertEqual(self.view._content, "Email: ${EMAIL}")
        sublime.status_message.assert_called_with("No backup found. Cannot reveal sensitive text.")

class TestToggleSensitiveTextCommand(unittest.TestCase):
    
    def setUp(self):
        self.view = MockSublimeView()
        self.view.run_command = MagicMock()
        sensitive_mappings.clear()
        global_settings.settings.clear()
        sublime.status_message.reset_mock()
    
    def test_toggle_hide_when_no_backup(self):
        edit = MagicMock()
        
        cmd = hide_sensitive_text.ToggleSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.view.run_command.assert_called_with('hide_sensitive_text')
    
    def test_toggle_reveal_when_backup_exists(self):
        sensitive_mappings[self.view.id_value] = {'original': 'test'}
        edit = MagicMock()
        
        cmd = hide_sensitive_text.ToggleSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.view.run_command.assert_called_with('reveal_sensitive_text')
    
    @patch('os.path.exists', return_value=True)
    def test_toggle_reveal_when_file_backup_exists(self, mock_exists):
        self.view._file_name = "/path/to/file.txt"
        edit = MagicMock()
        
        cmd = hide_sensitive_text.ToggleSensitiveTextCommand(self.view)
        cmd.run(edit)
        
        self.view.run_command.assert_called_with('reveal_sensitive_text')

class TestAddSensitivePatternCommand(unittest.TestCase):
    
    def setUp(self):
        self.window = MagicMock()
        global_settings.settings.clear()
        sublime.status_message.reset_mock()
    
    def test_add_pattern_flow(self):
        cmd = hide_sensitive_text.AddSensitivePatternCommand(self.window)
        cmd.run()
        self.window.show_input_panel.assert_called()
        
        cmd.on_pattern_entered(r'\b[A-Z]{3}\b')
        self.window.show_input_panel.assert_called()
        
        cmd.on_replacement_entered('${CODE}')
        
        patterns = global_settings.get('patterns', [])
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0]['pattern'], r'\b[A-Z]{3}\b')
        self.assertEqual(patterns[0]['replacement'], '${CODE}')
        sublime.save_settings.assert_called()
        sublime.status_message.assert_called()
    
    def test_empty_pattern_ignored(self):
        cmd = hide_sensitive_text.AddSensitivePatternCommand(self.window)
        cmd.run()
        self.window.show_input_panel.assert_called()
        
        cmd.on_pattern_entered("")
        self.assertEqual(self.window.show_input_panel.call_count, 1)

class TestSensitiveTextEventListener(unittest.TestCase):
    
    def setUp(self):
        sensitive_mappings.clear()
        global_settings.settings.clear()
        sublime.status_message.reset_mock()
    
    def test_cleanup_on_close(self):
        view = MockSublimeView()
        sensitive_mappings[view.id_value] = {'original': 'test'}
        
        listener = hide_sensitive_text.SensitiveTextEventListener()
        listener.on_close(view)
        
        self.assertNotIn(view.id_value, sensitive_mappings)
    
    def test_no_error_when_no_mapping(self):
        view = MockSublimeView()
        
        listener = hide_sensitive_text.SensitiveTextEventListener()
        listener.on_close(view)
        
        self.assertNotIn(view.id_value, sensitive_mappings)

if __name__ == '__main__':
    unittest.main()