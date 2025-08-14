#!/usr/bin/env python3

import re
import json
import sys
import os
import argparse

DEFAULT_PATTERNS = [
    {'pattern': r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', 'replacement': '${EMAIL}'},
    {'pattern': r'\b(?:\d{4}[-\s]?){3}\d{4}\b', 'replacement': '${CREDIT_CARD}'},
    {'pattern': r'\b(?!000-00-0000)\d{3}-\d{2}-\d{4}\b', 'replacement': '${SSN}'},
    {'pattern': r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', 'replacement': '${IP_ADDRESS}'},
    {'pattern': r'\b(?i:api[_-]?key[_-]?)[a-zA-Z0-9]{16,}\b', 'replacement': '${API_KEY}', 'flags': re.IGNORECASE},
    {'pattern': r'\bpassword\s*[:=]\s*[\'\"]?([^\'\"\s]+)[\'\"]?', 'replacement': '${PASSWORD}', 'flags': re.IGNORECASE},
]

def hide_sensitive_text(file_path, patterns=None):
    if patterns is None:
        patterns = DEFAULT_PATTERNS
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    if not content or content.isspace():
        return
    
    replacements = []
    
    for pattern_config in patterns:
        pattern = pattern_config.get('pattern')
        replacement = pattern_config.get('replacement', '${HIDDEN}')
        flags = pattern_config.get('flags', 0)
        
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
        backup_file = file_path + '.sensitive_backup'
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        mapping_file = file_path + '.sensitive_map'
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(replacements, f, indent=2)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Hidden {len(replacements)} sensitive text occurrences")
        print(f"Backup saved to: {backup_file}")
        print(f"Mapping saved to: {mapping_file}")
    else:
        print("No sensitive text found to hide")

def reveal_sensitive_text(file_path):
    backup_file = file_path + '.sensitive_backup'
    mapping_file = file_path + '.sensitive_map'
    
    if os.path.exists(backup_file):
        with open(backup_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        try:
            os.remove(backup_file)
            if os.path.exists(mapping_file):
                os.remove(mapping_file)
        except:
            pass
        
        print("Sensitive text revealed")
    else:
        print("No backup file found. Cannot reveal sensitive text.")

def load_custom_patterns(patterns_file):
    with open(patterns_file, 'r', encoding='utf-8') as f:
        patterns_data = json.load(f)
    
    patterns = []
    for p in patterns_data:
        flags = 0
        if 'flags' in p:
            if isinstance(p['flags'], str):
                flag_parts = p['flags'].split('|')
                for part in flag_parts:
                    part = part.strip()
                    if part in ['IGNORECASE', 'I']:
                        flags |= re.IGNORECASE
                    if part in ['MULTILINE', 'M']:
                        flags |= re.MULTILINE
                    if part in ['DOTALL', 'S']:
                        flags |= re.DOTALL
            else:
                flags = p['flags']
        
        patterns.append({
            'pattern': p['pattern'],
            'replacement': p.get('replacement', '${HIDDEN}'),
            'flags': flags
        })
    
    return patterns

def main():
    parser = argparse.ArgumentParser(description='Hide or reveal sensitive text in files')
    parser.add_argument('action', choices=['hide', 'reveal'], help='Action to perform')
    parser.add_argument('file', help='File to process')
    parser.add_argument('--patterns', help='JSON file with custom patterns')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    if args.action == 'hide':
        patterns = DEFAULT_PATTERNS
        if args.patterns:
            if os.path.exists(args.patterns):
                patterns = load_custom_patterns(args.patterns)
            else:
                print(f"Warning: Patterns file '{args.patterns}' not found. Using default patterns.")
        
        hide_sensitive_text(args.file, patterns)
    elif args.action == 'reveal':
        reveal_sensitive_text(args.file)

if __name__ == '__main__':
    main()