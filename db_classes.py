import pdb
import os,sqlite3
from datetime import datetime
from collections import defaultdict
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

    # sort a list of synonymous codon by less->more GC counts
    def _sort_Codon_list_by_GC(self,codon_list):
        gc_count_list = []
        for codon in codon_list:
            gc_count = 0
            for char in codon:
                if char == 'C' or char == 'G':
                    gc_count += 1   
            gc_count_list.append(gc_count)
        return [codon for gc_count,codon in sorted(   zip(gc_count_list,codon_list)  )]
    
    # generate a codon table that each codon list is sorted by less->more GC counts 
    def generate_OneLetter_to_codon_dict(self):
        sql_template = 'select OneLetter,Codon from codon;'
        cur = self.db.execute(sql_template)
        OneLetter_to_Codon_dict = defaultdict(list)
        for fields in cur.fetchall():
            OneLetter = fields[0]
            Codon = fields[1]
            OneLetter_to_Codon_dict[OneLetter].append(Codon)   
        for k,v in OneLetter_to_Codon_dict.iteritems():
            OneLetter_to_Codon_dict[k] = self._sort_Codon_list_by_GC(v) 
        return OneLetter_to_Codon_dict

    def __init__(self,DATABASE):
        self.db = sqlite3.connect(DATABASE)
        #OneLetter_to_Codon_dict = self.generate_OneLetter_to_codon_dict()
        #pdb.set_trace()
        #a = 1
