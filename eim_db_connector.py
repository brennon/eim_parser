from pymongo import MongoClient
# from eim_parser import EIMParserLogger

def recursive_update(old_dict, new_dict):
    """
    Recursively merges all keys of new_dict into old_dict, replacing duplicate keys
    in old_dict with values from new_dict.

    >>> d1 = {'songs':{'order':['zero','one','two']},'id':42,'unchanged':{'user':'admin'}}
    >>> d2 = {'songs':{'timestamps':[2,0,1]},'id':43,'rookie':16}
    >>> recursive_update(d1, d2)
    >>> d1 == {'songs':{'order':['zero','one','two'],'timestamps':[2,0,1]},'id':43,'rookie':16,'unchanged':{'user':'admin'}}
    True
    """
    for k in new_dict.keys():
        if k in old_dict and type(old_dict[k]) == type(dict()):
            recursive_update(old_dict[k], new_dict[k])
        else:
            old_dict[k] = new_dict[k]

class EIMDBConnector():
    def __init__(self, logger=None):
        self._client = None
        self.logger = logger

    def connect(self, hostname='muse.cc.vt.edu', port=27017):
        """
        Connects to the EiM database.

        >>> c = EIMDBConnector()
        >>> c.connect()

        >>> del c
        >>> c = EIMDBConnector()
        >>> c.connect('thishostshouldnot.exist.right.com') # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        pymongo.errors.ConnectionFailure:
        """
        try:
            self._client = MongoClient(hostname, port)
        except:
            self.logger.log('Could not connect to database on %s:%d' % (hostname, port), 'FAILURE')
            raise

    def disconnect(self):
        """
        Disconnects from the EiM database.
        """
        self._client.disconnect()

    def find_by_session_id(self, session_id, database='eim', collection='sessions'):
        """
        Finds and returns a document from a collection by session ID.

        >>> c = EIMDBConnector()
        >>> c.connect()
        >>> c.authenticate_to_database('eim', 'eim', 'emotoheaven')
        >>> c.find_by_session_id(-1) == None
        True
        >>> res = c.upsert_by_session_id(123456789, {'session_id':123456789})
        >>> c.find_by_session_id(123456789)['session_id'] == 123456789
        True
        >>> res = c.remove_by_session_id(123456789)
        """
        db = self._client[database]
        return db["%s" % collection].find_one({'session_id':session_id})

    def remove_by_session_id(self, session_id, database='eim', collection='sessions'):
        """
        Removes a document from a collection by session ID.

        >>> c = EIMDBConnector()
        >>> c.connect()
        >>> c.authenticate_to_database('eim', 'eim', 'emotoheaven')
        >>> res = c.upsert_by_session_id(123456789, {'session_id':123456789})
        >>> res = c.remove_by_session_id(123456789)
        >>> res['n']
        1
        >>> res['err'] == None
        True
        >>> c.find_by_session_id(123456789)
        """
        db = self._client[database]
        return db["%s" %collection].remove({'session_id':session_id})

    def upsert_by_session_id(self, session_id, document, database='eim', collection='sessions'):
        """
        Updates or inserts a document into a collection by session ID.

        >>> c = EIMDBConnector()
        >>> c.connect()
        >>> c.authenticate_to_database('eim', 'eim', 'emotoheaven')
        >>> res = c.upsert_by_session_id(123456789, {'session_id':123456789})
        >>> import random
        >>> n = random.random()

        >>> c.find_by_session_id(123456789)['updated_key']
        Traceback (most recent call last):
            ...
        KeyError: 'updated_key'

        >>> res = c.upsert_by_session_id(123456789, {'updated_key':n})
        >>> res['err'] == None
        True
        >>> res['n']
        1
        >>> c.find_by_session_id(123456789)['updated_key'] == n
        True

        >>> res = c.upsert_by_session_id(123456789, {'updated_key':n+1})
        >>> res['err'] == None
        True
        >>> res['n']
        1
        >>> c.find_by_session_id(123456789)['updated_key'] == n + 1
        True

        >>> res = c.remove_by_session_id(123456789)
        """
        db = self._client[database]
        existing_document = self.find_by_session_id(session_id, database, collection)

        if not existing_document:
            existing_document = {}

        recursive_update(existing_document, document)

        try:
            find_result = db["%s" % collection].update({'session_id':session_id}, existing_document, upsert=True)
            return find_result
        except:
            self.logger.log('Could find or update document with session ID: %s' % session_id, 'WARN')

    def authenticate_to_database(self, database, username, password):
        """
        Authenticates to database using username and password.

        >>> c = EIMDBConnector()
        >>> c.connect()
        >>> c.authenticate_to_database('eim', 'eim', 'emotoheaven')
        """
        db = self._client[database]
        try:
            db.authenticate(username, password)
        except PyMongoError:
            self.logger.log('Could not authenticate to database', 'FAILURE')
            raise

def __test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    __test()
