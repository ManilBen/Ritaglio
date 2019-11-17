import re
from nltk.corpus import stopwords
try :
	import cpickle as pickle
except :
	import pickle
import string
from collections import defaultdict
import timeit
import re
from math import log10

class extraction():
	
	def __init__(self,requests,collection=None):
		self.requests = r"cacm\query.text"
		self.collection = collection

	def requests_processing(self,request):
		file = open(request).read()
		regex = re.compile(r'\.W(.+?)\.[N|A]', re.DOTALL)
		return re.findall(regex,file)

	def create_index_req(self, rq):
		weightedIndex = self.get_weighted()

		requests = self.requests_processing(rq)
		stop = set(stopwords.words('english'))
		reqDict={}
		for i in range(0,len(requests)):
			reqNbr = str(i+1)
			reqDict[reqNbr]=defaultdict(int)
			for word in self.preprocess(i,requests,0): 
				if word not in stop :
					if word in weightedIndex:
						reqDict[reqNbr][word]=log10(len(self.get_index().keys())/len(weightedIndex[word]))
		return reqDict


	def collection_processing(self,collection):
		file = open(collection).read()
		#regex = re.compile(r'\.T[^\.](.+?)(?:\.W\n(.+?)|\.B)\.[B|A]', re.DOTALL)
		regex = re.compile(r'\.T\n(.+?)(?:\.W\n(.+?))?\.B\n', re.DOTALL)
		#regex = re.compile(r'\.T[^\.](.+?)\.W\n(.+?)\.[B|A]\n', re.DOTALL)
		docs = re.findall(regex,file)
		filtered = [(d[0],d[1]) for d in docs if not len(d[1])==0 ]
		return filtered

	def preprocess(self,i,col,verb):
		if verb == 1 :
			sentence = col[i][1].lower().replace(r"\n", " ")
		else : 
			sentence = col[i].lower().replace(r"\n", " ")
		sentence = re.sub(r"[\/()&~£{}%_:+*\"\]\[,.;@#-?!&$«»]|[1-9]+\ *", " ", sentence)
		return re.split(r'\s+', sentence) # split if encounters 1 space or more

	def create_index(self,number):
		documents = self.collection_processing(r"cacm\cacm.all")
		stop = set(stopwords.words('english'))
		inverse={}
		col={}
		for i in range(0,number):
			doc = re.sub(r"[\/()&~£{}%_:+*\"\]\[,.;@#-?!&$«»\n]|[1-9]+\ *", " ", documents[i][0])+str(i+1)
			col[doc]=defaultdict(int)
			col[doc]['max']=0
			for word in self.preprocess(i,documents,1): 
				if word not in stop : #  it uses the dictionary's hashing contrarly to using .key()
					col[doc][word]+=1
					if (col[doc][word]>col[doc]['max']):
						col[doc]['max']=col[doc][word]
					if word in inverse:
						if doc not in inverse[word]:
							inverse[word][doc]+=1
					else:
						inverse[word]=defaultdict(int)
						inverse[word][doc]+=1
		file = open('inversed.pkl', 'wb')
		pickle.dump(inverse,file)
		file.close()
		file = open('index.pkl', 'wb')
		pickle.dump(col,file)
		file.close()
		return col

	def get_index(self):
		file = open('index.pkl', 'rb')
		st = pickle.load(file)
		file.close()
		return st
			

	def get_inverse(self):
		file = open('inversed.pkl', 'rb')
		st = pickle.load(file)
		file.close()
		return st

	def get_weighted(self):
		file = open('weighted.pkl', 'rb')
		wg = pickle.load(file)
		file.close()
		return wg

	def weighted_index(self,number):
		index = get_index()
		inverse = get_inverse()
		weighted_index = {}
		for word in inverse:
			for doc in inverse[word]:
				weighted_index[word]=defaultdict(int)
				freq = inverse[word][doc]
				if freq == 0:
					weighted_index[word][doc]=0
				else :
					max_doc = index[doc]['max'] # retourne la freq max dans dans le doc
					doc_number = len(inverse[word]) # nbr de docs qui contiennent word
					weighted_index[word][doc]+=float(freq) / (float(max_doc)*log10(number/doc_number) + 1.0) #poids(ti, dj)=(freq(ti,dj)/Max(freq(t, dj))*Log((N/ni) +1)
		print(weighted_index)
		file = open('weighted.pkl', 'wb')
		pickle.dump(weighted,file)

class retrieval():
	
	def __init__(self,extraction,collection=None):
		self.extraction = extraction
		self.collection = collection

	def requetebydocument(self, document):
		index = self.extraction.get_index()
		document=document-1
		print("Liste des termes du document d"+str(document))
		for word in index['d'+str(document)].keys():
			print(word,'frequence :'+str(index['d'+str(document)][word]))


	def requetebyterme(self, terme):
		terme=terme.lower()
		number=0
		index_inverse=self.extraction.get_inverse()
		liste_docs = []
		if terme not in index_inverse:
			return None
		else :
			for wdoc in index_inverse[terme].keys():
				print('Document : " '+wdoc+'" Frequence du terme '+terme+' : '+str(index_inverse[terme][wdoc]))
				liste_docs.append(wdoc)
			return liste_docs

	def binary_model(self, request):
		request=request.lower()
		number=0
		requete = re.split(r'\s+', request)
		liste_zeros = list(map(lambda x: '0' if x not in ['and','or','not'] else x, requete))
		try:
			eval(" ".join(liste_zeros))
		except SyntaxError:
			return None

		liste_docs=defaultdict(list)
		documents = []
		expression = []
		i=0
		for r in requete:
			resultat = requetebyterme(r)
			if r not in ['and','or','not'] and resultat!=None:
				for doc in resultat:
					if doc not in liste_docs:
						liste_docs[doc]=liste_zeros
					liste_docs[doc][i]='1'
			i+=1
		print(liste_docs)
		docs_valides = []
		for doc in liste_docs :
			expression = " ".join(liste_docs[doc])
			if (eval(expression) == 1):
				docs_valides.append(doc)
		print(docs_valides)

if __name__== '__main__':
	ext = extraction(r"cacm\query.txt")
	print(ext.create_index_req(r"cacm\query.text"))
	#ext.create_index(1584)
	#ret = retrieval(ext)
	#ret.requetebyterme("program")
	