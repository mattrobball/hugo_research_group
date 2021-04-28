import argparse
import urllib
import bibtexparser 
import feedparser
import yaml
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import subprocess 
import time

arxiv_search_base = 'http://export.arxiv.org/api/query?search_query='

def attach_sum_id (article):
    author_list = []
    for author in article['authors']:
        author_list.append(''.join(['au:',author['last']]))
    author_query = '+AND+'.join(author_list)
    title_encode = article['title'].encode('ascii', 'ignore')
    title = title_encode.decode()
    title_list = '%20'.join(title.split())
    title_query = ''.join(['ti:',title_list,'&max_results=10'])
    target1 = ''.join([arxiv_search_base,author_query,'+AND+',title_query])
    with urllib.request.urlopen(target1) as search:
        xml = search.read()
    parsed_xml = feedparser.parse(xml)
    score = 0.0
    summary = ''
    arxiv_id = ''
    title = ''
    for entry in parsed_xml['entries']:
        if fuzz.ratio(article['title'].lower(),entry['title'].lower()) >= fuzz.ratio(article['title'].lower(),title.lower()):
            title = entry['title']
            summary = entry['summary']
            arxiv_id = entry['id'].replace('http://arxiv.org/abs/','')
    target2 = ''.join([arxiv_search_base,title_query])
    with urllib.request.urlopen(target2) as search:
        xml = search.read()
    parsed_xml = feedparser.parse(xml)
    for entry in parsed_xml['entries']:
        if fuzz.ratio(article['title'].lower(),entry['title'].lower()) >= fuzz.ratio(article['title'].lower(),title.lower()):
            title = entry['title']
            summary = entry['summary']
            arxiv_id = entry['id'].replace('http://arxiv.org/abs/','')
    print(article['title'])
    print(title)
    print(fuzz.ratio(article['title'].lower(),title.lower()))
    if fuzz.ratio(article['title'].lower(),title.lower()) >= 90:
        article['abstract'] = summary 
        article['arxiv_id'] = arxiv_id 

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
    editors = []
    for name in ref['editor']:
        split_name = bibtexparser.customization.splitname(name)
        authors.append({'first':' '.join(split_name['first']),'last':split_name['last'][0]})
    ref['editors'] = editors
    ref.pop('editor')
    attach_sum_id(ref)
    if 'arxiv_id' in ref.keys():
        pdf = ''.join([ref['arxiv_id'],'.pdf'])
        first_page = ''.join([ref['arxiv_id'],'_p1'])
        first_page_pdf = ''.join([first_page,'.pdf'])
        first_page_png = ''.join([first_page,'.png'])
        pointer = ''.join(['https://arxiv.org/pdf/',pdf])
        subprocess.run(['wget','--user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:21.0) Gecko/20100101 Firefox/21.0"]',pointer])
        subprocess.run(['pdftk', pdf, 'cat','1-1', 'output', first_page_pdf])
        subprocess.run(['pdftoppm', '-scale-to', '150', '-png', first_page_pdf, first_page])
        pic = ''.join([first_page,'-1','.png'])
        ref['image'] = pic
        subprocess.run(['mv',pic,'../static/images/publications/'])
        time.sleep(5)
    filename = ''.join([ref['ID'],'.md'])
    with open(filename,'w') as f:
        f.write('---\n')
        yaml.dump(ref,f,default_flow_style=False)
        f.write('---\n')