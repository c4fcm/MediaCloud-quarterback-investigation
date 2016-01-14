import datetime, json, string, logging, os, codecs
import unicodecsv as csv
import textmining, mediacloud, stopwords
from ConfigParser import SafeConfigParser

ROWS_PER_QUERY = 500000

# Load config data
parser = SafeConfigParser()
parser.read('config.txt')
MY_API_KEY = parser.get('API','MY_API_KEY')
mc = mediacloud.api.AdminMediaCloud(MY_API_KEY) #AdminMediaCloud, rather than MediaCloud

logging.basicConfig(level=logging.DEBUG)

t = open('qb-table.csv')
qb_table = csv.reader(t)
qb_table.next()

m = open('sources.csv')
media_reader = csv.reader(m)
media = [x[1] for x in media_reader][1:]
media_id_str = " ".join(media)
logging.info("Searching in %d media (%s)" % (len(media),media_id_str))
stopwords = stopwords.getStopWords()

def fetch_corpus_from_mc(team,qb): #MC query, returns list of words 
    '''
    Query MC for coverage of the QB specified, return a large string corpus
    '''
    logging.info('  querying for %s (%s)...' % (qb,team))
    words = []
    qb_split = qb.split()
    exclude = list(string.punctuation)+qb_split+team.split()+byteify(stopwords)+['1','2','3','4','5','6','7','8','9','0']
    exclude = [x.lower() for x in exclude]
    more = True
    start = 0
    while more:
        logging.debug('    starting at %d' % start)
        sentences = mc.sentenceList(solr_query=str('"'+qb+'"'), 
            solr_filter=[mc.publish_date_query(datetime.date(2015,9,9), datetime.date(2016,1,4)), 
                         '+media_id:('+media_id_str+')'], rows = ROWS_PER_QUERY, start=0)
        more = len(sentences['response']['docs'])==ROWS_PER_QUERY
        start = start + ROWS_PER_QUERY
    logging.info('    found %d sentences',len(sentences['response']['docs']))
    response = sentences['response']
    docs = response['docs']
    logging.info('  done')
    return " ".join([d['sentence'] for d in docs])

def load_qb_corpus(team, qb):
    corpora_dir = os.path.join('data','corpora')
    qb_corpora_path = os.path.join(corpora_dir,qb+'.txt')
    if not os.path.exists(corpora_dir):
        os.makedirs(corpora_dir)
    if os.path.exists(qb_corpora_path):
        f = codecs.open(qb_corpora_path, 'r', encoding='utf-8')
        corpus = f.read()
    else:
        corpus = fetch_corpus_from_mc(team,qb) 
        f = codecs.open(qb_corpora_path, 'w', encoding='utf-8')
        f.write(corpus)
    return corpus

def get_and_write_data():
    '''
    Call this to collect and output the data
    '''
    corpus = {}
    count_corpus = {}
    white_doc = ""
    other_doc = ""
    logging.info('Fetching sentences...')
    tdm_names = []
    tdm = textmining.TermDocumentMatrix()
    race_tdm_names = []
    race_tdm = textmining.TermDocumentMatrix()
    for row in qb_table:
        team = row[0]
        qb = row[1]
        race = row[2]
        file_label = str(qb+' ('+team+')')
        qb_corpus = load_qb_corpus(team,qb) 
        tdm.add_doc(qb_corpus)
        tdm_names.append(qb)
        if race == 'white':
            white_doc += qb_corpus + " "
        else:
            other_doc += qb_corpus + " "
    logging.info('done')
    # write the results
    logging.info('Writing results...')
    write_csv(tdm_names, tdm.rows(cutoff=1), 'word_freq_by_quarterback.csv')
    race_tdm.add_doc(white_doc)
    race_tdm.add_doc(other_doc)
    write_csv(['white','other'], race_tdm.rows(cutoff=1), 'word_freq_by_race.csv')
    logging.info('done')

def write_csv(cols, doc_iterator, filename):
    '''
    Write the results of a TDM to a CSV in a human-usable format
    '''
    words = doc_iterator.next()
    counts = [ row for row in doc_iterator ]
    output_csv = csv.writer( open( os.path.join('data',filename), 'wb') )
    output_csv.writerow(['word']+cols+[c+" pct" for c in cols])
    for idx in range(0,len(words)):
        word_counts = [ r[idx] for r in counts ]
        normalized_word_counts = [ float(r[idx])/float(len(words)) for r in counts ]
        output_csv.writerow([words[idx]]+word_counts+normalized_word_counts)

def byteify(input):
    '''
    Generic string helper function
    '''
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input
        
if __name__ == "__main__":
    get_and_write_data()
