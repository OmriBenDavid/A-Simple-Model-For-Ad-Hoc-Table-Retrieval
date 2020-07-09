# A-Simple-Model-For-Ad-Hoc-Table-Retrieval
By Omri Ben David & Dan Bublitsky

In this Project we implemented a simple weighted score model for Ad-Hoc table retrieval using Pylucene.

We used the WikiTables Dataset which can be found here:
https://github.com/iai-group/www2018-table

And the Pylucene library can be downloaded here:
https://lucene.apache.org/pylucene/

And Installation guide can be found here:
https://lxsay.com/archives/365

And for stop-word removal we used the nltk library. 
Download guide can be found here:
https://www.guru99.com/download-install-nltk.html

Our project consists of two main functions which handle the indexing and retrieval

in the TableIndexer function we:
1) Implemented stop-word removal as the text pre-processing
2) Broke each file in the data set into individual tables
3) Took the relevant fields from the tables which are:
  a) pgTitle - the actual table name, a strong inicator of relevance
  b) title - an array of the colomn titles, has some importance
  c) secondTitle - the second title of the table, has some importance.
  
we Indexed each field separately in order to support separate retrieval and scoring.

In the TableRetriever function we:
1) Removed stop-words from queries
2) Parsed the queries through three differen parsers (one for each field)
3) Recieved the top 1000 documents for each field
4) Used a hash table (default dictionary in python) to calculate the weighted score for each document 
5) Printed the top 20 tables for each query into the results.txt file using the TREC format.
