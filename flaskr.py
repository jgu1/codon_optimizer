#all the imports

import pdb
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
import esearch_fetch_parse
from contextlib import closing
from time import sleep
from flask.ext.paginate import Pagination
import re
import socket
from datetime import datetime,timedelta
# configuration
DATABASE = '/Users/jialianggu/WorkSpace/job_10_19/pubmed_search/pubmed_cache.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME_PASSWORD_DICT={'hao':'genome','jiashun':'genome','erxin':'genome','jun':'genome','yanqiu':'genome','jialiang':'genome'}
PAPER_PER_PAGE=10


app = Flask(__name__)
app.config.from_object(__name__)

#app = Blueprint('papers',__name__)

def connect_db():
    db =  sqlite3.connect(app.config['DATABASE'])
    #db.text_factory = str
    return db
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('create_pubmed_cache.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def fetch_db_for_search_terms(disease,genes_included,genes_excluded):
    papers=[]
    count_dict={}
    disease = '+'.join(disease.split())
    for gene in genes_included:
        search_term = 'AND+' + disease + '+' + gene
        if not not genes_excluded:
            search_term += '+NOT+'+ '+'.join(genes_excluded)

        papers_for_curr_search_term = fetch_db_for_one_search_term(search_term)
        count_dict[gene]=len(papers_for_curr_search_term)
        papers += papers_for_curr_search_term
    return papers,count_dict

def fetch_db_for_one_search_term(search_term):
    sql_fetch_all_papers_for_search_term = ('with paper_ids as' 
         ' (select paper_id from search_terms as S ,term_paper_relation as T' 
         ' where S.search_term="'+ search_term +'" and S.id = T.term_id)' 
         ' select title,link,authors_str,journal_title,publish_time_str,abstract,keywords_str from paper_ids, papers' 
         ' where paper_ids.paper_id = papers.id;')
    cur = g.db.execute(sql_fetch_all_papers_for_search_term)
    papers = [dict(title=row[0], link=row[1], authors_str=row[2],journal_title=row[3],publish_time_str=row[4],abstract=row[5],keywords_str=row[6],search_term=search_term) for row in cur.fetchall()]
    return papers

def delete_db_for_one_search_term(search_term):
    sql_delete_all_papers_for_search_term = ('with paper_ids as' 
         ' (select paper_id from search_terms as S ,term_paper_relation as T' 
         ' where S.search_term="'+ search_term +'" and S.id = T.term_id)' 
         ' delete from papers' 
         ' where papers.id in paper_ids;')
    cur = g.db.execute(sql_delete_all_papers_for_search_term)
    
    sql_delete_all_term_paper_relations_for_search_term = ('with term_ids as'
        ' (select term_id from term_paper_relation as T, search_terms as S'
        ' where T.term_id = S.id and S.search_term="' + search_term + '") '
        ' delete from term_paper_relation'
        ' where term_paper_relation.term_id in term_ids ; ')
    cur = g.db.execute(sql_delete_all_term_paper_relations_for_search_term)

    sql_delete_search_terms_for_search_term = ('delete from search_terms'
        ' where search_terms.search_term="' + search_term + '" ;'
        )
    cur = g.db.execute(sql_delete_search_terms_for_search_term)
    g.db.commit()

def highlight_search_terms(abstract, search_term):
    terms = re.split('\+|AND|OR',search_term)
    terms = filter(bool,terms)
    for term in terms:
        abstract = abstract.replace(term,'<mark>'+term+'</mark>')
    return abstract

@app.route('/')
def show_papers():
   
    if 'disease' not in session or 'genes_included' not in session:
        return render_template('show_papers.html')

 
    disease = session['disease']
    genes_included = session['genes_included']
    genes_excluded = session['genes_excluded']

    all_papers,count_dict = fetch_db_for_search_terms(disease,genes_included,genes_excluded)
  
    #begin pagination 
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    PAPER_PER_PAGE= app.config['PAPER_PER_PAGE'] 
    papers_for_this_page = all_papers[(page-1)*PAPER_PER_PAGE:page*PAPER_PER_PAGE] 
    
    for paper in papers_for_this_page:
        abstract = paper['abstract']
        if abstract is not None:
            paper['abstract'] = highlight_search_terms(abstract,paper['search_term'])
    
    pagination = Pagination(page=page, total=len(all_papers), per_page=PAPER_PER_PAGE, record_name='papers')
    #end pagination
    return render_template('show_papers.html',papers=papers_for_this_page,count_dict=count_dict,pagination=pagination)


def pop_db(disease,genes_included,genes_excluded):
    
    disease='+'.join(disease.split())
 
    for gene in genes_included:
        search_term = 'AND+' + disease + '+' + gene
        if not not genes_excluded:
            search_term += '+NOT+'+ '+'.join(genes_excluded)
        #pdb.set_trace()
        sql_check_if_search_term_has_results_already = ('select last_update from search_terms'
             ' where search_term="' + search_term +'"')
        cur = g.db.execute(sql_check_if_search_term_has_results_already)
        result = cur.fetchall()
        if len(result) > 0:
            time_delta = datetime.now() - datetime.strptime(result[0][0], "%Y-%m-%d %H:%M:%S.%f")
            if time_delta.seconds > 60*60*4: # re-fetch if the record is older than 1 day
                delete_db_for_one_search_term(search_term)
                esearch_fetch_parse.Main(DATABASE,search_term,gene)
        else:
            esearch_fetch_parse.Main(DATABASE,search_term,gene)

def parse_web_search_term(web_search_term_disease,web_search_term_genes_included,web_search_term_genes_excluded):
    disease = web_search_term_disease.strip()
    genes_included = web_search_term_genes_included.strip().split()
    genes_excluded = web_search_term_genes_excluded.strip().split()
    return disease,genes_included,genes_excluded

@app.route('/search', methods=['POST'])
def search():
 
    if not session.get('logged_in'):
        abort(401)
    
    web_search_term_disease = request.form['disease']
    web_search_term_genes_included  = request.form['genes_included']
    web_search_term_genes_excluded = request.form['genes_excluded']
    
    if web_search_term_disease is None or web_search_term_genes_included is None:
        return render_template('show_papers.html')
   
    disease,genes_included,genes_excluded = parse_web_search_term(web_search_term_disease,web_search_term_genes_included,web_search_term_genes_excluded)


    pop_db(disease,genes_included, genes_excluded)
 
    session['disease']=disease
    session['genes_included']=genes_included
    session['genes_excluded']=genes_excluded

    return redirect(url_for('show_papers'))

@app.route('/choose_term', methods=['GET'])
def choose_term():
    gene=request.args.get('gene', 1)
    session['genes_included']=[gene]
    return redirect(url_for('show_papers'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] not in app.config['USERNAME_PASSWORD_DICT']:
            error = 'Invalid username'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_papers'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_papers'))

if __name__ == '__main__':
    ip_for_current_machine = socket.gethostbyname(socket.gethostname())
    app.run(host=ip_for_current_machine,port=55555,threaded=True)


