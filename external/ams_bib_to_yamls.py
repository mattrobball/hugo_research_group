import argparse
import bibtexparser 
import yaml

inputparser = argparse.ArgumentParser(description='Split input .bib file into separate markdown files with yaml front matter ')

inputparser.add_argument('file',type=str,help='The path to the bib file')

args = inputparser.parse_args()

with open(args.file) as bibfile:
    bib_data = bibtexparser.load(bibfile)

for ref in bib_data.entries:
    bibtexparser.customization.convert_to_unicode(ref)
    ref['entry'] = ref.pop('ENTRYTYPE')
    if 'url' in ref.keys():
        ref['hyperlink'] = ref.pop('url')
    for key in ref:
        ref[key] = ref[key].replace('\n',' ')
    msc = ref['mrclass'].replace('(','')
    msc = msc.replace(')','')
    msc = msc.split()
    ref['mrclass'] = {'primary': msc[0], 'secondary': msc[1:]} 
    bibtexparser.customization.author(ref)
    authors = []
    for name in ref['author']:
        split_name = bibtexparser.customization.splitname(name)
        authors.append({'first':' '.join(split_name['first']),'last':split_name['last'][0]})
    ref['authors'] = authors
    ref.pop('author')
    filename = ''.join([ref['ID'],'.md'])
    with open(filename,'w') as f:
        f.write('---\n')
        yaml.dump(ref,f,default_flow_style=False)
        f.write('---\n')