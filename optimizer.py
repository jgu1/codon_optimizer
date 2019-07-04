import pdb
from collections import defaultdict
def optimize_AA(AA_sequence,db):
    #pdb.set_trace()
    OneLetter_to_codon_dict = generate_OneLetter_to_codon_dict(db)
    gc_count,length = 0.0,0.0
    sequence = [None] * len(AA_sequence) * 3
    
    first_codon = OneLetter_to_codon_dict[AA_sequence[0]][0]
    gc_count += count_GC_in_codon(first_codon)
    length += 3
    sequence[:3] = first_codon
    for i in range(1,len(AA_sequence)):
        AA = AA_sequence[i]
        codons = OneLetter_to_codon_dict[AA]
        codon = codons[0] # default low GC
        if gc_count / length < 0.5:
            codon = codons[-1]
        gc_count += count_GC_in_codon(codon)
        length += 3
        sequence[i*3:i*3+3] = codon
           
    #pdb.set_trace()
    #a = 1

    return ''.join(sequence)
 
 # sort a list of synonymous codon by less->more GC counts
def _sort_Codon_list_by_GC(codon_list):
    gc_count_list = []
    for codon in codon_list:
           gc_count = count_GC_in_codon(codon)
           gc_count_list.append(gc_count)
    return [codon for gc_count,codon in sorted(   zip(gc_count_list,codon_list)  )]

# generate a codon table that each codon list is sorted by less->more GC counts 
def generate_OneLetter_to_codon_dict(db):
    sql_template = 'select OneLetter,Codon from codon;'
    cur = db.execute(sql_template)
    OneLetter_to_Codon_dict = defaultdict(list)
    for fields in cur.fetchall():
        OneLetter = fields[0]
        Codon = fields[1]
        OneLetter_to_Codon_dict[OneLetter].append(Codon)   
    for k,v in OneLetter_to_Codon_dict.iteritems():
        OneLetter_to_Codon_dict[k] = _sort_Codon_list_by_GC(v) 
    return OneLetter_to_Codon_dict

def count_GC_in_codon(codon):
    gc_count = 0
    for char in codon:
        if char == 'C' or char == 'G':
            gc_count += 1
    return gc_count   

def lookup_AA_nucleo(AA_sequence,db):
    sql_template = 'select AA_sequence,nucleo_sequence from AA_nucleo where AA_sequence = "' + AA_sequence + '";'
    cur = db.execute(sql_template)
    result = None
    for fields in cur.fetchall():
        AA_sequence = fields[0]
        nucleo_sequence = fields[1]
        if nucleo_sequence is not None:
            result = nucleo_sequence
    return result

def insert_AA_nucleo(AA_sequence,nucleo_sequence,db):
    sql_template = 'insert into AA_nucleo (AA_sequence,nucleo_sequence) values (?,?)'
    try:
        db.cursor().execute(sql_template,[AA_sequence,nucleo_sequence])
    except sqlite3.ProgrammingError:
        db.cursor().execute(sql_template,[unicode(AA_sequence),unicode(nucleo_sequence)])
    db.commit()
