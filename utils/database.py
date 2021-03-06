import os
import json
from utils import rchop, encode_dict

TABLE_SUFFIX = ".tab"

class Group():
    def __init__(self):
        pass
        
    def exists(self, path):
        print path
        if len(path) == 0:
            return True
        if path[0] in self.tables:
            return self.tables[path[0]].exists(path[1:])
        return False
        

class Table(Group):
    def __init__(self, name, parent=None, data=None):
        self.name = name if name.endswith(TABLE_SUFFIX) else name + TABLE_SUFFIX
        self.parent = parent
        if data:
            self.write(data)
        elif not os.path.exists(self.name):
            self.write("{}")

    def read(self):
        with open(self.name) as df:
            return json.load(df, encoding='utf-8', object_hook=encode_dict)
            
    def write(self, data):
        with open(self.name, 'w') as df:
            json.dump(data, df, encoding='utf-8', indent=4)
    
    def drop(self):
        os.remove(self.name)
    
    def get_value(self, path, field):
        if len(path) > 0:
            return None
        return self.read().get(field, None)
    
    def get_data(self, path):
        if len(path) > 0:
            return None
        return self.read()
       

class Database(Group):
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.tables = {}
        if not os.path.isdir(name):
            os.makedirs(name)
        else:
            for filename in os.listdir(name):
                table_path = self._path_to(filename)
                if filename.endswith(TABLE_SUFFIX):
                    self.tables[rchop(filename, TABLE_SUFFIX)] = Table(table_path)
                elif os.path.isdir(table_path):
                    self.tables[filename] = Database(table_path)
                  
    def _path_to(self, name):
        return os.path.join(self.name, name)
                  
    def __str__(self):
        return str(self.tables)
        
    def table(self, name, create=True):
        name = rchop(name, TABLE_SUFFIX)
        if not name in self.tables and create:
            self.tables[name] = Table(self._path_to(name), self)
        return self.tables.get(name, None)
        
    def group(self, name, create=True):
        if not name in self.tables and create:
            self.tables[name] = Database(self._path_to(name), self)
        return self.tables.get(name, None)

    def drop(self, name=None, flush=True):
        if name != None:
            if name in self.tables:
                if flush:
                    self.tables[name].drop()
                self.tables.pop(name)
        else:
            for t in self.tables:
                self.tables[t].drop()
            self.tables.clear()
            os.rmdir(self.name)
            
    def get_value(self, path, field):
        if len(path) == 0 or not path[0] in self.tables:
            return None
        return self.tables[path[0]].get_value(path[1:], field)
        
    def get_data(self, path):
        if len(path) == 0 or not path[0] in self.tables:
            return None
        return self.tables[path[0]].get_data(path[1:])
        
    def create(self, path, data):
        if len(path) == 1:
            self.tables[path[0]] = Table(self._path_to(path[0]), self, data)
        else:
            if not path[0] in self.tables:
                self.tables[path[0]] = Database(self._path_to(path[0]), self)
            self.tables[path[0]].create(path[1:], data)
    
    def delete(self, path):
        if len(path) == 1:
            self.drop(path[0])
        else:
            self.tables[path[0]].delete(path[1:])
