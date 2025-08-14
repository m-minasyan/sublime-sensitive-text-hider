import sublime
print("Loading SensitiveTextHider...")

try:
    from .hide_sensitive_text import *
    from .test_load import *
    from .diagnostic import *
    print("SensitiveTextHider imported successfully!")
except ImportError as e:
    print(f"Import error: {e}")
    try:
        from hide_sensitive_text import *
        from test_load import *
        from diagnostic import *
        print("SensitiveTextHider imported via fallback!")
    except ImportError as e2:
        print(f"Fallback import also failed: {e2}")