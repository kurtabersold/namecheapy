import requests
from xml.etree import ElementTree
import logging
import namecheap_secrets

# TODO: Prices Command=namecheap.users.getPricing&ProductType=DOMAIN



logfile='namecheap.log'
logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logging.info('\n\nStarting Namecheapy')
logging.getLogger("requests").setLevel(logging.WARNING) # Shut up Requests!
#logging.getLogger("urllib3").setLevel(logging.WARNING) # Shut up requests!


# Static config settings
from namecheap_secrets import * # namecheap_secrets.py has api key and user name
ClientIp = '10.10.10.10' # TODO
url = 'https://api.namecheap.com/xml.response'


# Config Settings
minLength = 1 # minimum length of domain prefix (before the dot)
requestSize = 500 # Number of domain names per request
maxLength = 5000 # Not used yet

# Variables we populate
tlds = []
names = []
available = []
namestring = ''

def getTlds():
  # Gets list of top-level domains, and returns a list
  # https://www.namecheap.com/support/api/methods/domains/get-tld-list.aspx
  Command = 'namecheap.domains.gettldlist'
  payload = {
    'ApiUser'  : ApiUser,
    'ApiKey'   : ApiKey,
    'UserName' : UserName,
    'Command'  : Command,
    'ClientIp' : ClientIp
    }
  r = requests.get(url, params=payload)
  logging.debug('API Request: %s', r.url)
  logging.debug('API Status Code: %s', r.status_code)
  logging.debug('API Response Time: %s API Command: %s', r.elapsed, Command)
  root = ElementTree.fromstring(r.content)
  tree = root[3]
  for tld in tree.iter():
    if 'Type' in tld.attrib: # TODO: Ghetto
      if 'Name' in tld.attrib:
        tlds.append(tld.attrib['Name'])
  logging.debug('TLDS: %s', tlds)
  logging.info('TLD Count: %s', len(tlds))

def getTldPrices():
  # Gets a few price details for non-premium TLDS
  # https://www.namecheap.com/support/api/methods/users/get-pricing.aspx
  Command = 'namecheap.users.getPricing'
  ProductType = 'DOMAIN'
  payload = {
    'ApiUser'     : ApiUser,
    'ApiKey'      : ApiKey,
    'UserName'    : UserName,
    'Command'     : Command,
    'ClientIp'    : ClientIp,
    'ProductType' : ProductType
    }
  r = requests.get(url, params=payload)
  logging.info('API Request: %s', r.url)
  logging.info('API Response Time: %s API Command: %s', r.elapsed, Command)
  root = ElementTree.fromstring(r.content)
  tree = root[3][0]
  for stuff in tree.iter():
    if 'Name' in stuff.attrib:
      print(dir(stuff))
      # ['__class__', '__copy__', '__deepcopy__', '__delattr__', '__delitem__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__getstate__', '__gt__', '__hash__', '__init__', '__le__', '__len__', '__lt__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setitem__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', 'append', 'clear', 'extend', 'find', 'findall', 'findtext', 'get', 'getchildren', 'getiterator', 'insert', 'items', 'iter', 'iterfind', 'itertext', 'keys', 'makeelement', 'remove', 'set']
      logging.info(stuff.attrib)


def parseWords(filename):
  # Reads list of words from file
  # Passes word to checkSpelling function to match a domain name
  # TODO: Allow reading list of words from other sources
  with open(filename, 'r') as f:
    words = [word.strip() for word in f] # Strip newlines from words
    logging.info('Checking %s words in list', len(words))
    for word in words:
      checkSpelling(tlds, word)


def checkSpelling(tlds, word):
  # Checks if a word ends with a top level domain
  # If word matches a TLD, and is at least minLength,
  # word is added to a list to be checked for availability
  for tld in tlds:
    if word.endswith(tld):
      prefix = word.rstrip(tld) # Strip tld from end of word
      suffix = tld
      fqdn = prefix + '.' + suffix # Form FQDN
      if len(prefix) >= minLength:
        names.append(fqdn)


def formatNames(names):
  # Takes a python list of domain names
  # Divides list into comma seperated strings
  # Lenth is limited to requestSize (TODO: Should this be # of domains, or # of characters?)
  # TODO: Research about how long the request sting can be.
  logging.info('Found %s possible domain names in word list', len(names))
  while names:
    sep=','
    namestring = sep.join(names[:requestSize])
    count = namestring.split(',') # Create a list, to get a count of domains, when we switch to character limit
    logging.info('Checking list of %s domains', len(count))
    logging.info('namestring lenth: %s characters', len(namestring))
    logging.debug('Checking the following domains: %s', count)
    checkDomains(namestring)
    del names[:requestSize]
    logging.info('%s names remain to be checked', len(names))


def checkDomains(words):
  # Takes a comma seperates string of domain names,
  # and checks availability. Populates 'available' variable
  # https://www.namecheap.com/support/api/methods/domains/check.aspx
  # TODO: Input validation
  DomainList = words
  Command = 'namecheap.domains.check'
  payload = {
  'ApiUser'    : ApiUser,
  'ApiKey'     : ApiKey,
  'UserName'   : UserName,
  'Command'    : Command,
  'ClientIp'   : ClientIp,
  'DomainList' : DomainList
  }
  r = requests.get(url, params=payload)
  logging.debug('API Request: %s', r.url)
  logging.info('API Response Time: %s API Command: %s', r.elapsed, Command)
  root = ElementTree.fromstring(r.content)
  tree = root[3]
  for domain in tree.iter():
    if 'Domain' in domain.attrib:
      if domain.attrib['Available'] == 'true':
        if domain.attrib['IsPremiumName'] == 'true':
          registrationPrice = domain.attrib['PremiumRegistrationPrice']
          renewalPrice = domain.attrib['PremiumRenewalPrice']
          transferPrice = domain.attrib['PremiumTransferPrice']
          logging.info('PRICING: Registration: %s Renewal: %s', registrationPrice, renewalPrice)
        # 'PremiumRenewalPrice': '25.9700', 'PremiumRegistrationPrice': '647.4000'
        logging.info('AVAILABLE: %s', domain.attrib['Domain']) # TODO: LOGGING!
        #logging.debug(domain.attrib)
        available.append(domain.attrib['Domain'])
      else:
        #logging.debug('Not Available: %s', domain.attrib['Domain'])
        pass


def getStarted(words):
  getTlds()
  #getTldPrices()
  parseWords(words)
  formatNames(names)
  logging.info('Available domains: %s', available)
getStarted('words.txt')
