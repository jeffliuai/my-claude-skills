import sys
from pathlib import Path

def clean_merged(input_path, output_path):
    content = Path(input_path).read_text(encoding='utf-8')
    # Split by the horizontal line used in create_inbox_note
    sections = content.split('---')
    
    cleaned_body = []
    current_section_body = []
    
    for s in sections:
        lines = s.strip().split('\n')
        if not lines: continue
        
        # Identify if this is a metadata section or body section
        is_metadata = any(any(line.strip().startswith(p) for p in ['source:', 'date:', 'type:', 'source :']) for line in lines)
        
        if is_metadata:
            continue
            
        # If it's a body section, skip the title line starting with # TG 摘錄
        # and also skip the footer tags
        for l in lines:
            if l.strip().startswith('# TG 摘錄：'): continue
            if l.strip().startswith('#TG/摘錄 #Inbox'): continue
            current_section_body.append(l)
            
    Path(output_path).write_text('\n'.join(current_section_body).strip(), encoding='utf-8')

if __name__ == "__main__":
    if len(sys.argv) > 2:
        clean_merged(sys.argv[1], sys.argv[2])
