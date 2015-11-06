import pdb
import sys
import urllib2
import re
import xml.etree.ElementTree as ET
from beans import Pubmed_Article
from db_classes import DAO
def do_esearch(Entrez_head,search_term):
    this_search = 'esearch.fcgi?/db=pubmed&term='+search_term+'&retmax=10000&usehistory=y'
    response = urllib2.urlopen(Entrez_head + this_search)
    xml_esearch = response.read()

    p_WebEnv = re.compile(r'<WebEnv>(.*)</WebEnv>')
    #pdb.set_trace()
    WebEnv = p_WebEnv.findall(xml_esearch)[0]
        
    p_queryKey = re.compile(r'<QueryKey>(.*)</QueryKey>')
    queryKey = p_queryKey.findall(xml_esearch)[0]

    return WebEnv,queryKey

def do_efetch(Entrez_head,WebEnv,queryKey):
    this_fetch = 'efetch.fcgi?db=pubmed&query_key='+ queryKey + '&WebEnv=' + WebEnv + '&retmode=xml'
    response = urllib2.urlopen(Entrez_head + this_fetch)
    xml_efetch = response.read()
    return xml_efetch

def parse_efetch_xml(efetch_result_xml_string):
    root = ET.fromstring(efetch_result_xml_string)
   
    paper_list=[]
 
    for medlineCitation in root.iter('MedlineCitation'):
        curr_paper=None
        # PMID
        PMID = medlineCitation.find('PMID').text
        # title
        article = medlineCitation.find('Article')
        title = article.find('ArticleTitle').text
        # abstract_text
        whole_abstract_text = None
        abstract = article.find('Abstract')
        if abstract is not None:
            whole_abstract_text = ''
            for abstract_text in abstract:
                whole_abstract_text += abstract_text.text
        # keywords_str
        keywords_str= None
        keywordList = medlineCitation.find('KeywordList')
        if keywordList is not None:
            keywords_str = ''
            for keyword in keywordList.iter('Keyword'):
                curr_keyword = keyword.text
                keywords_str += curr_keyword + ', '
            keywords_str = keywords_str[:-2] # remove the last ', '
        curr_paper = Pubmed_Article(title,PMID,whole_abstract_text,keywords_str)   
        paper_list.append(curr_paper)
    return paper_list

def Main(DATABASE,search_term):
    #DATABASE = '/Users/jialianggu/WorkSpace/job_10_19/Entrez_version/pubmed_cache.db' 
    dao = DAO(DATABASE)  
    Entrez_head = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
   
    WebEnv,queryKey = do_esearch(Entrez_head,search_term)  
    xml_efetch = do_efetch(Entrez_head,WebEnv,queryKey) 

    paper_list = parse_efetch_xml(xml_efetch)
   
     
    #pdb.set_trace()
    
    num_papers = len(paper_list)
    term_id=dao.insert_one_search_term_into_table_search_terms(search_term,num_papers)   
    for paper in paper_list:
        paper_id = dao.insert_one_paper_into_table_papers(paper.title,paper.link,paper.abstract,paper.keywords_str)
        dao.insert_one_relation_into_table_term_paper_relation(term_id,paper_id)    
    

    #pdb.set_trace()
    return paper_list

if __name__ == '__main__':
    DATABASE = sys.argv[1]
    search_term = sys.argv[2]
    Main(DATABASE,search_term)
