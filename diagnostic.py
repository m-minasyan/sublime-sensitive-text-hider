import sublime
import sublime_plugin

class SensitiveTextDiagnosticCommand(sublime_plugin.WindowCommand):
    def run(self):
        import sys
        import os
        
        msg = []
        msg.append("SensitiveTextHider Diagnostic")
        msg.append("=" * 40)
        msg.append(f"Python version: {sys.version}")
        msg.append(f"Sublime Text version: {sublime.version()}")
        msg.append(f"Package path: {os.path.dirname(__file__)}")
        msg.append("")
        msg.append("Available commands:")
        
        for cmd in dir(sublime_plugin):
            if "Command" in cmd:
                msg.append(f"  - {cmd}")
        
        msg.append("")
        msg.append("Loaded plugin classes:")
        
        try:
            from . import hide_sensitive_text
        except ImportError:
            import SensitiveTextHider.hide_sensitive_text as hide_sensitive_text
        
        for item in dir(hide_sensitive_text):
            if "Command" in item:
                msg.append(f"  - {item}")
        
        sublime.message_dialog("\n".join(msg))

def plugin_loaded():
    print("DIAGNOSTIC: SensitiveTextHider diagnostic.py loaded")
    window = sublime.active_window()
    if window:
        window.status_message("SensitiveTextHider diagnostic loaded")