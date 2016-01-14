import datetime, json, logging, os, codecs, re
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
logging.info("-----------------------------------------------------------------")
logging.info("Starting QB data gathering")

# build stopwords
my_stopwords = [word.lower() for word in stopwords.getStopWords()]
qb_table = csv.reader(codecs.open('qb-table.csv', 'r', 'utf-8'))
qb_table.next()
team_stopwords = []    
qb_stopwords = []
for row in qb_table:
    [ team_stopwords.append(word.lower()) for word in row[0].split() ]
    [ qb_stopwords.append(word.lower()) for word in row[1].split() ]
logging.debug(" Added qb names to stopwords: %s" % qb_stopwords)
logging.debug(" Added team names to stopwords: %s" % team_stopwords)
my_stopwords = my_stopwords + qb_stopwords + team_stopwords

# load media sources
m = codecs.open('sources.csv','r','utf-8')
media_reader = csv.reader(m)
media = [x[1] for x in media_reader][1:]
media_id_str = " ".join(media)
logging.info("Searching in %d media" % len(media))
logging.debug("media ids = %s" % media_id_str)

def fetch_corpus_from_mc(team,qb): #MC query, returns list of words 
    '''
    Query MC for coverage of the QB specified, return a large string corpus
    '''
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
    '''
    Grab the corpus for a QB from local data, or from MC if we don't have it yet
    '''
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

def tokenize_and_remove_stopwords(document):
    '''
    Callback to help the TDM creation via the textmining package
    '''
    document = document.lower() # do everything in lowercase
    document = re.sub('[^a-z]', ' ', document)  # remove non-alpha-numeric chars
    words = document.strip().split()
    before_word_count = len(words)
    # Remove stopwords
    words = [word for word in words if word not in my_stopwords]
    after_word_count = len(words)
    logging.debug("    %d (removed %d)" % (after_word_count,before_word_count-after_word_count))
    return words

def write_csv(cols, doc_iterator, filename):
    '''
    Write the results to a CSV in a human-usable format
    '''
    words = doc_iterator.next()
    word_freqs = [ row for row in doc_iterator ]
    corpus_word_count = [sum(row) for row in word_freqs]
    output_csv = csv.writer( codecs.open( os.path.join('data',filename), 'wb', 'utf-8') )
    output_csv.writerow(['word']+cols+[c+" pct" for c in cols])
    for idx in range(0,len(words)):
        word_counts = [ r[idx] for r in word_freqs ]
        normalized_word_counts = [ float(r[idx])/float(corpus_word_count[i]) for i,r in enumerate(word_freqs) ]
        output_csv.writerow([words[idx]]+word_counts+normalized_word_counts)

def get_and_write_data():
    '''
    Call this to collect and output the data
    '''
    corpus = {}
    count_corpus = {}
    white_doc = ""
    other_doc = ""
    logging.info('Loading sentences...')
    tdm_names = []
    tdm = textmining.TermDocumentMatrix(tokenize_and_remove_stopwords)
    race_tdm_names = []
    race_tdm = textmining.TermDocumentMatrix(tokenize_and_remove_stopwords)
    qb_table = csv.reader(codecs.open('qb-table.csv', 'r', 'utf-8'))
    qb_table.next()
    for row in qb_table:
        team = row[0]
        qb = row[1]
        race = row[2]
        logging.info('  %s (%s) - %s' % (qb,team,race))
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
    logging.info("Building white corpus")
    race_tdm.add_doc(white_doc)
    logging.info("Building non-white corpus")
    race_tdm.add_doc(other_doc)
    write_csv(['white','other'], race_tdm.rows(cutoff=1), 'word_freq_by_race.csv')
    logging.info('done')
        
if __name__ == "__main__":
    get_and_write_data()
