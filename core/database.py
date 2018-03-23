import os
import json
from utils.utils import rchop, encode_dict

TABLE_SUFFIX = ".tab"

class DatabaseException(Exception):
    pass
    
DATABASE = None     
class Database():
    @staticmethod    
    def initialize(name):
        global DATABASE
        DATABASE = Database(name)
        
    @staticmethod
    def instance():
        global DATABASE
        if DATABASE == None:
            raise DatabaseException("Database service was not initialized")
        return DATABASE

    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        
        self.namespaces = {}
        self.tables = {}
        
        if not os.path.isdir(self.name):
            os.makedirs(self.name)
        for filename in os.listdir(self.name):
            path = self._path_to(filename)
            if os.path.isdir(path):
                self.namespaces[filename] = path
            elif filename.endswith(TABLE_SUFFIX):
                self.tables[rchop(filename, TABLE_SUFFIX)] = path
     
    def __getitem__(self, key):
        return self.child(key)

    def _path_to(self, name):
        return os.path.join(self.name, name)
        
    def child(self, name):
        if name in self.namespaces:
            return Database(self.namespaces[name], self)
        elif name in self.tables:
            return Table(self.tables[name], self)
        return None
        
    def drop(self):
        self.children.clear()
        os.rmdir(self.name)
        if self.parent != None:
            self.parent.namespaces.pop(self.name)
        
    def drop(self, name):
        child = self.child(name)
        if child != None:
            child.drop()
        else:
            raise DatabaseException("Cannot drop '%s' as it does not exist." % name)
     
    def namespace(self, name, create=False):
        if not name in self.namespaces and create:
            self.namespaces[name] = self._path_to(name)
        path = self.namespaces.get(name, None)
        return Database(path, self) if path else None
    
    def table(self, name, create=False):
        if not name in self.tables and create:
            self.tables[name] = self._path_to(name)
        path = self.tables.get(name, None)
        return Table(path, self) if path else None

class Table():
    def __init__(self, name, parent, data=None):
        self.name = name if name.endswith(TABLE_SUFFIX) else name + TABLE_SUFFIX
        self.parent = parent
        if data:
            self.write(data)
        elif not os.path.exists(self.name):
            self.write("{}")
        self.data = self.read()

    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def read(self):
        with open(self.name) as df:
            return json.load(df, encoding='utf-8', object_hook=encode_dict)
            
    def save(self):
        self.write(self.data)
            
    def write(self, data):
        with open(self.name, 'w') as df:
            json.dump(data, df, encoding='utf-8', indent=4)
    
    def drop(self):
        os.remove(self.name)
        if self.parent != None:
            self.parent.tables.pop(self.name)