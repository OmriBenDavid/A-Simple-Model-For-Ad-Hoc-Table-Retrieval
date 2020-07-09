import json
import os, sys, glob
from collections import defaultdict, Counter
import lucene

#Importing Useful Lucene tools for indexing and retrieval
from java.nio.file import Paths
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.document import  Document, Field, FieldType
from org.apache.lucene.analysis.core import SimpleAnalyzer
from org.apache.lucene.index import IndexWriter, DirectoryReader, IndexWriterConfig, IndexOptions
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.search.similarities import Similarity, BM25Similarity
from org.apache.lucene.queryparser.classic import QueryParser

#Importing libraries for Stop-word-removal and Word-tokenization
import nltk
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize 

#In our data we have several interesting fields:
# for table in x - gives all table ids 
# x[table]["title"] - The colomn titles - not important but somewhat informative - will recieve the smallest weight
# x[table]["pgTitle"] - The actual table name - very informative - will recieve a large weight
# x[table]["secondTitle"] - Adds some discription - not very important but somewhat informative - will recieve a small weight
# x[table]["caption"] - Mostly identical to the second title - not informative - will not be indexed


def TableIndexer(docdir,indir):
    #Innitializing the lucene virtual machine
    lucene.initVM()

    DIRTOINDEX = docdir
    INDEXIDR = Paths.get(indir)

    #Innitializing the Index directory and Index writer
    indexdir = SimpleFSDirectory(INDEXIDR)
    analyzer = SimpleAnalyzer()
    conf = IndexWriterConfig(analyzer)
    index_writer = IndexWriter(indexdir,conf)

    #Using library function to define the stop-words
    stop_words = set(stopwords.words('english'))
    
    print("Indexing Started...")
    for tfile in glob.glob(os.path.join(DIRTOINDEX,'*.json')):
        with open(tfile) as json_file:
            print("Indexing: ",tfile)
            tables = json.load(json_file) # loading the tables from the current json file 
            for table_id in tables:
                table = tables[table_id] # loading the dable data
                titles = table["title"] # extrating the colomn titles
                titles = list(set(titles)) # removing duplicate values
                titles = ' '.join(titles) # joining to one string
                titles = word_tokenize(titles) # tokenization 
                titles = ' '.join([w for w in titles if not w in stop_words]) # stop-word removal

                pgTitle = table["pgTitle"] #extracting the table name
                pgTitle = word_tokenize(pgTitle) #tokeization
                pgTitle = ' '.join([w for w in pgTitle if not w in stop_words]) # stop-word removal

                secondTitle = table["secondTitle"] # Extracting the second title
                secondTitle = word_tokenize(secondTitle) # tokenization 
                secondTitle = ' '.join([w for w in secondTitle if not w in stop_words]) # stop work removal
                
                # Defining the ID field type - does not require indexing because it's not informative
                t_id = FieldType()
                t_id.setStored(True)
                t_id.setIndexOptions(IndexOptions.NONE)

                #Defining the field type of the other fields, require indexing and frequencies calculation
                t_content = FieldType()
                t_content.setStored(True)
                t_content.setIndexOptions(IndexOptions.DOCS_AND_FREQS)

                document = Document() # innitializing the new table document
                document.add(Field("id",table_id,t_id)) # adding ID fiels
                document.add(Field("titles",titles,t_content)) # adding titles field
                document.add(Field("pgTitle",pgTitle,t_content)) # adding page title field
                document.add(Field("secondTitle",secondTitle,t_content)) # adding second title field
                index_writer.addDocument(document) # writing complete document to index

    index_writer.close() 
    print("Indexing complete.")


def TableRetriever(indir, query_path):
    
    lucene.initVM() #innitializing the lucene virtual machine
    
    #Using library function to define the stop-words
    stop_words = set(stopwords.words('english'))

    #getting the directory and index searcher
    index_dir = SimpleFSDirectory(Paths.get(indir))
    analyzer = SimpleAnalyzer()
    searcher = IndexSearcher(DirectoryReader.open(index_dir))
    similarity = BM25Similarity() # for this model we use BM25 similarity score
    searcher.setSimilarity(similarity)

    titles_parser = QueryParser("titles",analyzer) # setting parser for scoring the titles
    pgTitle_parser = QueryParser("pgTitle",analyzer) # setting parser for scoring page titles
    secondTitle_parser = QueryParser("secondTitle",analyzer) # setting parser for scoring second titles

    with open(query_path) as q_file:
        query = q_file.readline()[2:] #reading the first line from the query file while removing the quety number
        query = word_tokenize(query) # tokenization 
        query = ' '.join([w for w in query if not w in stop_words])
        results = open("results.txt",'w') # setting the result file
        cnt = 1 # counter for query number
        while query:
            scores = defaultdict(lambda: 0) #setting hash-table for scoring all the retrieved documents
        
            q_titles = titles_parser.parse(query)
            q_pgTitle = pgTitle_parser.parse(query)
            q_secondTitle = secondTitle_parser.parse(query)

            titles_hits = searcher.search(q_titles, 1000).scoreDocs # getting the 1000 documents with the best scores for colomn titles
            for hit in titles_hits:
                doc_id = hit.doc # getting the document's id in the index
                score = hit.score # getting the document's score
                scores[doc_id] = scores[doc_id] + score * 0.15 # adding the score to it's current score for this query times the weight

            pgTitle_hits = searcher.search(q_pgTitle, 1000).scoreDocs # getting the 1000 documents with the best scores for page titles
            for hit in pgTitle_hits:
                doc_id = hit.doc # getting the document's id in the index
                score = hit.score # getting the document's score
                scores[doc_id] = scores[doc_id] + score * 0.75 # adding the score to it's current score for this query times the weight

            secondTitle_hits = searcher.search(q_secondTitle,1000).scoreDocs # getting the 1000 documents with the best scores for second titles
            for hit in secondTitle_hits:
                doc_id = hit.doc # getting the document's id in the index
                score = hit.score # getting the document's score
                scores[doc_id] = scores[doc_id] + score * 0.1 # adding the score to it's current score for this query times the weight

            sorted_scores = Counter(scores)
            top_docs = sorted_scores.most_common(20) # getting the top 20 documents after weighted score calculation 
            rank = 1
            # writing the results to the file
            for (key,scr) in top_docs:
                document = searcher.doc(key)
                t_id = document.get("id")
                results.write('\t'.join((str(cnt),"Q0",'{:>14}'.format(str(t_id)),str(rank),str(scr),"Omri&Dan\n")))
                rank = rank + 1
            cnt = cnt+1 # incrementing the query id
            query = q_file.readline() # reading the next query
        q_file.close()
        results.close()
        

TableIndexer("tables_redi2_1","index/")

TableRetriever("index/","queries.txt")
