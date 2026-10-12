with open('database/seed_recommendations_library_final.sql', encoding='utf-8-sig', errors='replace') as f:
    content = f.read()
 
content = content.replace('\u2014', '--')
content = content.replace('\u2013', '-')
content = content.replace('\u201c', '"')
content = content.replace('\u201d', '"')
content = content.replace('\u2019', "'")
content = content.replace('\u2018', "'")
content = content.replace('\u0090', '')
content = content.replace('\u009d', '')
 
with open('database/seed_recommendations_library_final.sql', 'w', encoding='utf-8') as f:
    f.write(content)
 
print('Done')
 