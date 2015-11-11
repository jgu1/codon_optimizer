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

    if 'No items found' in xml_esearch: #no need to continue
        return None,None

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
        if title is None:   # some papers written in foreign language doesn't have a title
            title = article.find('VernacularTitle').text 
         
        # authors_str
        authors_str = ''
        authorList = article.find('AuthorList')
        if authorList is not None:
            for author in authorList:
                curr_author = ''
                lastname = author.find('LastName')
                if lastname is not None:
                    curr_author += lastname.text
                forename = author.find('ForeName')
                if forename is not None:
                    curr_author += ' ' + forename.text + ', '
                authors_str += curr_author
            authors_str = authors_str[:-2] # remove the last ', '        
        
        # journal_title,publish_time_str
        journal_title = ''
        publish_time_str = ''
        journal = article.find('Journal')
        if journal is not None:
            journal_title = journal.find('Title').text
            journalIssue = journal.find('JournalIssue')
            if journalIssue is not None:
                pubDate = journalIssue.find('PubDate')
                if pubDate is not None:
                    publish_time_year = pubDate.find('Year')
                    if publish_time_year is not None:
                        publish_time_str = publish_time_year.text
 
        # abstract_text
        whole_abstract_text = None
        abstract = article.find('Abstract')
        if abstract is not None:
            whole_abstract_text = ''
            for abstract_text in abstract:
                if abstract_text is not None and abstract_text.text is not None:
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
        curr_paper = Pubmed_Article(title,PMID,authors_str,journal_title,publish_time_str,whole_abstract_text,keywords_str)   
        paper_list.append(curr_paper)
    return paper_list

def Main(DATABASE,search_term,gene):
    #DATABASE = '/Users/jialianggu/WorkSpace/job_10_19/Entrez_version/pubmed_cache.db' 
    dao = DAO(DATABASE)  
    Entrez_head = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
   
    paper_list = []

    WebEnv,queryKey = do_esearch(Entrez_head,gene)
    if WebEnv is not None and queryKey is not None: 
        WebEnv,queryKey = do_esearch(Entrez_head,search_term)  
        xml_efetch = do_efetch(Entrez_head,WebEnv,queryKey) 
        paper_list = parse_efetch_xml(xml_efetch)       
 
    num_papers = len(paper_list)
    term_id=dao.insert_one_search_term_into_table_search_terms(search_term,num_papers)   
    for paper in paper_list:
        paper_id = dao.insert_one_paper_into_table_papers(paper.title,paper.link,paper.authors_str,paper.journal_title,paper.publish_time_str,paper.abstract,paper.keywords_str)
        dao.insert_one_relation_into_table_term_paper_relation(term_id,paper_id)    
    

    #pdb.set_trace()
    return paper_list

if __name__ == '__main__':
    DATABASE = sys.argv[1]
    search_term = sys.argv[2]
    Main(DATABASE,search_term)
