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
# configuration
DATABASE = '/Users/jialianggu/WorkSpace/job_10_19/pubmed_search/pubmed_cache.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME_PASSWORD_DICT={'jialiang':'password','hao':'password','jiashun':'password','erxin':'password','jun':'password','yanqiu':'password'}
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


def search_db_for_search_term(search_term):
    sql_fetch_all_papers_for_search_term = ('with paper_ids as' 
         ' (select paper_id from search_terms as S ,term_paper_relation as T' 
         ' where S.search_term="'+ search_term +'" and S.id = T.term_id)' 
         ' select title,link,authors_str,journal_title,publish_time_str,abstract,keywords_str from paper_ids, papers' 
         ' where paper_ids.paper_id = papers.id;')
    cur = g.db.execute(sql_fetch_all_papers_for_search_term)
    papers = [dict(title=row[0], link=row[1], authors_str=row[2],journal_title=row[3],publish_time_str=row[4],abstract=row[5],keywords_str=row[6]) for row in cur.fetchall()]
    return papers


def highlight_search_terms(abstract, search_term):
    terms = re.split('\+|AND|OR',search_term)
    terms = filter(bool,terms)
    for term in terms:
        abstract = abstract.replace(term,'<span>'+term+'</span>')
    return abstract

@app.route('/')
def show_papers():
   
    if not 'search_term' in session:
        return render_template('show_papers.html')
 
    search_term = session['search_term']
    all_papers = search_db_for_search_term(search_term)
   
  
    #begin pagination 
    search = False
    q = request.args.get('q')
    if q:
        search = True
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

        

    PAPER_PER_PAGE= app.config['PAPER_PER_PAGE'] 
    papers_for_this_page = all_papers[(page-1)*PAPER_PER_PAGE:page*PAPER_PER_PAGE] 
    for paper in papers_for_this_page:
        abstract = paper['abstract']
        if abstract is not None:
            paper['abstract'] = highlight_search_terms(abstract,search_term)
    pagination = Pagination(page=page, total=len(all_papers), per_page=PAPER_PER_PAGE, search=search, record_name='papers')
    #end pagination
    return render_template('show_papers.html',papers=papers_for_this_page,pagination=pagination)

@app.route('/search', methods=['POST'])
def search():
 
    if not session.get('logged_in'):
        abort(401)
    
    web_search_term_and = request.form['search_term_and'].strip()
    web_search_term_or  = request.form['search_term_or'].strip()
    web_search_term_not = request.form['search_term_not'].strip()
    
    if web_search_term_and is None and web_search_term_or is None:
        return render_template('show_papers.html')   
    
    search_term = ''
    if not not web_search_term_and:
        search_term += 'AND+'  + '+'.join(web_search_term_and.split())
    if not not web_search_term_or:
        search_term += '+OR+' + '+'.join(web_search_term_or.split())
    if not not web_search_term_not:
        search_term += '+NOT+'+ '+'.join(web_search_term_not.split())
    #pdb.set_trace()
    sql_check_if_search_term_has_results_already = ('select count(1) from search_terms'
         ' where search_term="' + search_term +'"')
    cur = g.db.execute(sql_check_if_search_term_has_results_already)
    result_count = cur.fetchall()[0][0]
    if result_count < 1:
        esearch_fetch_parse.Main(DATABASE,search_term)

    session['search_term'] = search_term

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


