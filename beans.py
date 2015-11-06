class Pubmed_Article(object):
    PUBMED_HEADER = 'http://www.ncbi.nlm.nih.gov/pubmed/' # static variable
    title=''
    link=''
    abstract=None
    keywords_str=None

    def __init__(self,title,PMID,abstract,keywords_str):
        self.title=title
        self.link=Pubmed_Article.PUBMED_HEADER + str(PMID)
        self.abstract = abstract
        self.keywords_str = keywords_str
        
    

