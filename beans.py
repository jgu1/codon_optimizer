class Pubmed_Article(object):
    PUBMED_HEADER = 'http://www.ncbi.nlm.nih.gov/pubmed/' # static variable
    title=''
    link=''
    authors_str=''
    journal_title=''
    publish_time_str=''
    abstract=None
    keywords_str=None

    def __init__(self,title,PMID,authors_list,journal_title,publish_time_str,abstract,keywords_str):
        self.title=title
        self.link=Pubmed_Article.PUBMED_HEADER + str(PMID)
        self.authors_str=authors_list
        self.journal_title=journal_title
        self.publish_time_str=publish_time_str
        self.abstract = abstract
        self.keywords_str = keywords_str
        
    

