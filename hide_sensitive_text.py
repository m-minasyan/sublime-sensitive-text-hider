import sublime
import sublime_plugin
import re
import json
import os

sensitive_mappings = {}

def plugin_loaded():
    settings = sublime.load_settings('SensitiveTextHider.sublime-settings')
    if not settings.has('patterns'):
        default_patterns = [
            {
                "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "replacement": "${EMAIL}"
            },
            {
                "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
                "replacement": "${CREDIT_CARD}"
            },
            {
                "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
                "replacement": "${SSN}"
            },
            {
                "pattern": r"\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
                "replacement": "${IP_ADDRESS}"
            },
            {
                "pattern": r"\bapi[_-]?key[_-]?[a-zA-Z0-9]{20,}\b",
                "replacement": "${API_KEY}",
                "flags": "IGNORECASE"
            },
            {
                "pattern": r"\bpassword\s*[:=]\s*['\"]?[^'\"\s]+['\"]?",
                "replacement": "${PASSWORD}",
                "flags": "IGNORECASE"
            }
        ]
        settings.set('patterns', default_patterns)
        sublime.save_settings('SensitiveTextHider.sublime-settings')

class HideSensitiveTextCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if not view:
            return
        view.run_command('hide_sensitive_text_impl')

class HideSensitiveTextImplCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view_id = self.view.id()
        file_name = self.view.file_name()
        
        settings = sublime.load_settings('SensitiveTextHider.sublime-settings')
        patterns = settings.get('patterns', [])
        
        if not patterns:
            patterns = [
                {'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'replacement': '${EMAIL}'},
                {'pattern': r'\b(?:\d{4}[-\s]?){3}\d{4}\b', 'replacement': '${CREDIT_CARD}'},
                {'pattern': r'\b\d{3}-\d{2}-\d{4}\b', 'replacement': '${SSN}'},
                {'pattern': r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', 'replacement': '${IP_ADDRESS}'},
                {'pattern': r'\bapi[_-]?key[_-]?[a-zA-Z0-9]{20,}\b', 'replacement': '${API_KEY}', 'flags': re.IGNORECASE},
            ]
        
        content = self.view.substr(sublime.Region(0, self.view.size()))
        original_content = content
        
        if file_name:
            backup_file = file_name + '.sensitive_backup'
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(original_content)
        else:
            if view_id not in sensitive_mappings:
                sensitive_mappings[view_id] = {}
            sensitive_mappings[view_id]['original'] = original_content
        
        replacements = []
        
        for pattern_config in patterns:
            pattern = pattern_config.get('pattern')
            replacement = pattern_config.get('replacement', '${HIDDEN}')
            flags = pattern_config.get('flags', 0)
            
            if isinstance(flags, str):
                flags_value = 0
                if 'IGNORECASE' in flags or 'I' in flags:
                    flags_value |= re.IGNORECASE
                if 'MULTILINE' in flags or 'M' in flags:
                    flags_value |= re.MULTILINE
                flags = flags_value
            
            matches = list(re.finditer(pattern, content, flags))
            
            for match in reversed(matches):
                original_text = match.group(0)
                replacements.append({
                    'start': match.start(),
                    'end': match.end(),
                    'original': original_text,
                    'replacement': replacement
                })
                
                content = content[:match.start()] + replacement + content[match.end():]
        
        if replacements:
            if file_name:
                mapping_file = file_name + '.sensitive_map'
                with open(mapping_file, 'w', encoding='utf-8') as f:
                    json.dump(replacements, f, indent=2)
            else:
                if view_id not in sensitive_mappings:
                    sensitive_mappings[view_id] = {}
                sensitive_mappings[view_id]['replacements'] = replacements
            
            self.view.replace(edit, sublime.Region(0, self.view.size()), content)
            
            sublime.status_message(f"Hidden {len(replacements)} sensitive text occurrences")
        else:
            sublime.status_message("No sensitive text found to hide")

class RevealSensitiveTextCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if not view:
            return
        view.run_command('reveal_sensitive_text_impl')

class RevealSensitiveTextImplCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view_id = self.view.id()
        file_name = self.view.file_name()
        
        restored = False
        
        if file_name:
            backup_file = file_name + '.sensitive_backup'
            mapping_file = file_name + '.sensitive_map'
            
            if os.path.exists(backup_file):
                with open(backup_file, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                self.view.replace(edit, sublime.Region(0, self.view.size()), original_content)
                
                try:
                    os.remove(backup_file)
                    if os.path.exists(mapping_file):
                        os.remove(mapping_file)
                except:
                    pass
                
                restored = True
        else:
            if view_id in sensitive_mappings and 'original' in sensitive_mappings[view_id]:
                original_content = sensitive_mappings[view_id]['original']
                self.view.replace(edit, sublime.Region(0, self.view.size()), original_content)
                del sensitive_mappings[view_id]
                restored = True
        
        if restored:
            sublime.status_message("Sensitive text revealed")
        else:
            sublime.status_message("No backup found. Cannot reveal sensitive text.")

class ToggleSensitiveTextCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if not view:
            return
        view.run_command('toggle_sensitive_text_impl')

class ToggleSensitiveTextImplCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view_id = self.view.id()
        file_name = self.view.file_name()
        
        has_backup = False
        if file_name:
            backup_file = file_name + '.sensitive_backup'
            has_backup = os.path.exists(backup_file)
        else:
            has_backup = view_id in sensitive_mappings and 'original' in sensitive_mappings[view_id]
        
        if has_backup:
            self.view.run_command('reveal_sensitive_text_impl')
        else:
            self.view.run_command('hide_sensitive_text_impl')

class AddSensitivePatternCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel(
            "Enter regex pattern to hide:",
            "",
            self.on_pattern_entered,
            None,
            None
        )
    
    def on_pattern_entered(self, pattern):
        if pattern:
            self.pattern = pattern
            self.window.show_input_panel(
                "Enter replacement variable (e.g., ${VAR_NAME}):",
                "${HIDDEN}",
                self.on_replacement_entered,
                None,
                None
            )
    
    def on_replacement_entered(self, replacement):
        settings = sublime.load_settings('SensitiveTextHider.sublime-settings')
        patterns = settings.get('patterns', [])
        
        patterns.append({
            'pattern': self.pattern,
            'replacement': replacement,
            'flags': 0
        })
        
        settings.set('patterns', patterns)
        sublime.save_settings('SensitiveTextHider.sublime-settings')
        sublime.status_message(f"Added pattern: {self.pattern} -> {replacement}")

class SensitiveTextEventListener(sublime_plugin.EventListener):
    def on_close(self, view):
        view_id = view.id()
        if view_id in sensitive_mappings:
            del sensitive_mappings[view_id]