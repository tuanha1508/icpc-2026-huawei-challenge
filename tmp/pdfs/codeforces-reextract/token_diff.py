import re, difflib, unicodedata
from pathlib import Path

def clean(path):
    s=Path(path).read_text(errors='replace')
    start=s.find('This is an interactive scheduling problem')
    if start>=0:s=s[start:]
    # Remove obvious page chrome and the new change-notification overlay.
    lines=[]
    for line in s.splitlines():
        x=line.strip()
        if re.search(r'https://codeforces\.com/',x): continue
        if re.match(r'^\d+/\d+/\d+,',x): continue
        if re.match(r'^\d+/\d+$',x): continue
        if x in {'Problem -A- Codeforces','Problems - Codeforces','×'}: continue
        if 'The problem statement has recently been changed' in x: continue
        if x in {'changes. changes.','changes.'}: continue
        lines.append(line)
    s=' '.join(lines)
    s=s.replace('\u00ad','').replace('–','-').replace('—','-').replace('−','-')
    s=re.sub(r'\s+',' ',s)
    # Keep words/numbers/protocol punctuation; lowercase for layout-neutral alignment.
    return re.findall(r'[A-Za-z_]+|\d+(?:\.\d+)?|<=|>=|->|\S',s.lower())
old=clean('tmp/pdfs/codeforces-reextract/old-raw.txt')
new=clean('tmp/pdfs/codeforces-reextract/new-raw.txt')
print('tokens',len(old),len(new))
sm=difflib.SequenceMatcher(None,old,new,autojunk=False)
ops=sm.get_opcodes(); print('ratio',sm.ratio(),'opcodes',len(ops))
for tag,i1,i2,j1,j2 in ops:
    if tag=='equal': continue
    a=old[i1:i2];b=new[j1:j2]
    # Only show locally aligned edits; huge blocks are extraction-order changes.
    if len(a)>120 or len(b)>120:
        print(f'\n[{tag} old {i1}:{i2} ({len(a)}) new {j1}:{j2} ({len(b)}) -- LARGE LAYOUT BLOCK]')
        continue
    print(f'\n[{tag} old {i1}:{i2} new {j1}:{j2}]')
    print('OLD:', ' '.join(a))
    print('NEW:', ' '.join(b))
