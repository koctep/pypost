import sys
import re
import textwrap

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.splitlines()
    new_lines = []
    in_code_block = False
    
    # Pre-process to consolidate lines for wrapping? 
    # Markdown paragraphs are separated by blank lines. 
    # It's easier to parse logical blocks.
    
    # Simple state machine approach
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Code block detection
        if line.strip().startswith('```') or line.strip().startswith('~~~'):
            in_code_block = not in_code_block
            new_lines.append(line)
            i += 1
            continue
            
        if in_code_block:
            new_lines.append(line)
            i += 1
            continue
            
        # Table detection (heuristic: starts and ends with |)
        if line.strip().startswith('|'):
            new_lines.append(line)
            i += 1
            continue
            
        # Headers
        if line.strip().startswith('#'):
            # Ensure empty line before if not first line
            if new_lines and new_lines[-1].strip() != '':
                new_lines.append('')
            
            new_lines.append(line)
            
            # Ensure empty line after (will be handled by next iteration logic or explicit check)
            # Actually, we can just ensure we push an empty line if the next line is not empty
            if i + 1 < len(lines) and lines[i+1].strip() != '':
                # We can't insert into input 'lines', but we can append empty to new_lines
                # But we handle "empty line before" of the NEXT element usually.
                # Let's just append an empty line now if we want to enforce it immediately.
                new_lines.append('') 
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}$', line.strip()):
             new_lines.append(line)
             i += 1
             continue
        
        # Empty lines
        if not line:
            # Collapse multiple empty lines?
            if new_lines and new_lines[-1].strip() == '':
                pass # Already has empty line
            else:
                new_lines.append('')
            i += 1
            continue

        # List items
        # Match bullets: - or * or +
        # Match ordered: 1. or 2. etc
        # We also need to handle indentation.
        
        list_match = re.match(r'^(\s*)([-*+]|\d+\.)(\s+)(.*)', line)
        if list_match:
            indent = list_match.group(1)
            marker = list_match.group(2)
            space = list_match.group(3)
            text = list_match.group(4)
            
            # Standardize marker
            if re.match(r'\d+\.', marker):
                marker = '1.'
            
            # Consistent list bullets? Rule says "Use - or * (be consistent)". 
            # We won't force change existing * to - or vice versa unless we track global state.
            # Let's keep what is there for bullets, but fix numbers.
            
            prefix = f"{indent}{marker}{space}"
            subsequent_indent = " " * len(prefix)
            
            # Check if we need to merge subsequent lines that are part of this item?
            # In MD, subsequent lines of a list item can be just indented or not.
            # Simple wrapping of the single line:
            
            wrapped = textwrap.fill(text, width=100, initial_indent=prefix, subsequent_indent=subsequent_indent, break_long_words=False, break_on_hyphens=False)
            new_lines.append(wrapped)
            i += 1
            continue

        # Blockquotes
        if line.lstrip().startswith('>'):
             # Wrap blockquotes?
             # They are tricky because of > prefixes on every line.
             new_lines.append(line)
             i += 1
             continue

        # Regular text paragraph
        # We should try to consume subsequent text lines to re-wrap the paragraph.
        # But that's dangerous if we mix up separate things.
        # For now, let's just wrap the current line if it's long.
        
        if len(line) > 100:
             # Preserve indentation?
             indent_match = re.match(r'^(\s*)', line)
             indent = indent_match.group(1) if indent_match else ""
             
             wrapped = textwrap.fill(line, width=100, initial_indent=indent, subsequent_indent=indent, break_long_words=False, break_on_hyphens=False)
             new_lines.append(wrapped)
        else:
             new_lines.append(line)
        i += 1

    # Final cleanup
    # Remove multiple consecutive empty lines
    final_lines = []
    for l in new_lines:
        if not l.strip() and final_lines and not final_lines[-1].strip():
            continue
        final_lines.append(l)
        
    # Ensure single final newline
    output = "\n".join(final_lines).rstrip() + "\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(output)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            print(f"Formatting {arg}...")
            process_file(arg)

