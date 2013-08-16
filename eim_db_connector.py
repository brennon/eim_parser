from pymongo import MongoClient

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
    def __init__(self):
        self._client = None

    def connect(self, hostname='data.musicsensorsemotion.com', port=27017):
        """
        Connects to the EiM database.

        >>> c = EIMDBConnector()
        >>> c.connect()
        True

        >>> del c
        >>> c = EIMDBConnector()
        >>> c.connect('thishostshouldnot.exist.right.com')
        False
        """
        try:
            self._client = MongoClient(hostname, port)
            return True
        except:
            return False

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
        True
        >>> c.authenticate_to_database('test', 'eim', 'testest123')
        True
        >>> c.find_by_session_id(-1, 'test', 'test') == None
        True

        >>> c.find_by_session_id(123456789, 'test', 'test')['session_id'] == 123456789.0
        True
        """
        db = self._client[database]
        return db["%s" % collection].find_one({'session_id':session_id})

    def remove_by_session_id(self, session_id, database='eim', collection='sessions'):
        """
        Removes a document from a collection by session ID.

        >>> c = EIMDBConnector()
        >>> c.connect()
        True
        >>> c.authenticate_to_database('test', 'eim', 'testest123')
        True
        >>> upsert_result = c.upsert_by_session_id(12345677, {'session_id':12345677}, 'test', 'test')
        >>> upsert_result['err'] == None
        True
        >>> upsert_result['n']
        1
        >>> remove_result = c.remove_by_session_id(12345677, 'test', 'test')
        >>> remove_result['n']
        1
        >>> remove_result['err'] == None
        True

        >>> c.find_by_session_id(12345677, 'test', 'test') == None
        True
        """
        db = self._client[database]
        return db["%s" %collection].remove({'session_id':session_id})

    def upsert_by_session_id(self, session_id, document, database='eim', collection='sessions'):
        """
        Updates or inserts a document into a collection by session ID.

        >>> c = EIMDBConnector()
        >>> c.connect()
        True
        >>> c.authenticate_to_database('test', 'eim', 'testest123')
        True
        >>> import random
        >>> n = random.random()
        >>> upsert_result = c.upsert_by_session_id(123456789, {'updated_key':n}, 'test', 'test')
        >>> upsert_result['err'] == None
        True
        >>> upsert_result['n']
        1
        >>> c.find_by_session_id(123456789, 'test', 'test')['updated_key'] == n
        True

        >>> upsert_result = c.upsert_by_session_id(123456789, {'updated_key':n+1}, 'test', 'test')
        >>> upsert_result['err'] == None
        True
        >>> upsert_result['n']
        1
        >>> c.find_by_session_id(123456789, 'test', 'test')['updated_key'] == n
        False

        >>> upsert_result = c.upsert_by_session_id(123456788, {'session_id':123456788}, 'test', 'test')
        >>> upsert_result['err'] == None
        True
        >>> upsert_result['n']
        1
        >>> c.find_by_session_id(123456788, 'test', 'test')['session_id']
        123456788
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
            return None

    def authenticate_to_database(self, database, username, password):
        """
        Authenticates to database using username and password.

        >>> c = EIMDBConnector()
        >>> c.connect()
        True
        >>> c.authenticate_to_database('test', 'eim', 'testest123')
        True
        """
        db = self._client[database]
        return db.authenticate(username, password)

def __test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    __test()
