import os
import pickle

from lore.stores.base import Base
from lore.util import timer


class Disk(Base):
    EXTENSION = '.pickle'
    
    def __init__(self, dir):
        self.dir = dir
        self.limit = None
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
    
    def __getitem__(self, key):
        if key in self:
            with timer('read %s:' % key):
                with open(self._path(key), 'rb') as f:
                    return pickle.load(f)
        return None
    
    def __setitem__(self, key, value):
        with timer('write %s:' % key):
            with open(self._path(key), 'wb') as f:
                pickle.dump(value, f)
        
        if self.limit is not None:
            with timer('evict: %s' % key):
                while self.size() > self.limit:
                    del self[self.lru()]
    
    def __delitem__(self, key):
        os.remove(self._path(key))
    
    def __contains__(self, key):
        return os.path.isfile(self._path(key))
    
    def __len__(self):
        return len(self.keys())
    
    def size(self):
        return sum(os.path.getsize(f) for f in self.values())
    
    def keys(self):
        return [self._key(f) for f in os.listdir(self.dir)]
    
    def values(self):
        return [os.path.join(self.dir, f) for f in os.listdir(self.dir)]
    
    def lru(self):
        files = sorted(self.values(), key=lambda f: os.stat(f).st_atime)
        
        if not files:
            return None
        
        return self._key(files[0])
    
    def _path(self, key):
        return os.path.join(self.dir, key + self.EXTENSION)
    
    def _key(self, path):
        return os.path.basename(path)[0:-len(self.EXTENSION)]