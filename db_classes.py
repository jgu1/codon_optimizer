import pdb
import os,sqlite3
from datetime import datetime
class DAO(object):
    db = None    

    def insert_one_search_term_into_table_search_terms(self,search_term,result_count):
        sql_template = 'insert into search_terms(search_term,num_papers,last_update) values(?,?,?)'
        #insert
        try:
            cursor = self.db.execute(sql_template,[search_term,result_count,datetime.now()])
        except sqlite3.ProgrammingError:
            cursor = self.db.execute(sql_template,[unicode(search_term),unicode(result_count),datetime.now()])
            self.db.commit()
        #get primary_key
        return cursor.lastrowid

    def insert_one_paper_into_table_papers(self,title,link,authors_str,journal_title,publish_time_str,abstract,keywords_str):
        #insert
        sql_template = 'insert into papers (title,link,authors_str,journal_title,publish_time_str,abstract,keywords_str) values(?,?,?,?,?,?,?)'
        try:
            cursor = self.db.execute(sql_template,[title,link,authors_str,journal_title,publish_time_str,abstract,keywords_str])
       
        except sqlite3.ProgrammingError:
            cursor = self.db.execute(sql_template,[unicode(title),unicode(link),unicode(authors_str),unicode(journal_title),unicode(publish_time_str),unicode(abstract),unicode(keywords_str)])
            
        self.db.commit()
        #get primary_key
        return cursor.lastrowid

    def insert_one_relation_into_table_term_paper_relation(self,term_id,paper_id):
        sql_template = 'insert into term_paper_relation (term_id, paper_id) values(?,?)'
        self.db.execute(sql_template,[term_id,paper_id])
        self.db.commit()

    def __init__(self,DATABASE):
        self.db = sqlite3.connect(DATABASE)