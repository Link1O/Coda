# tools.pyx
# cython: language_level=3
cdef class DynamicDictManager:
    cdef dict _dicts

    def __cinit__(self):
        self._dicts = {}

    cpdef void set_item(self, str name, int key, object value):
        if name not in self._dicts:
            self._dicts[name] = {}
        self._dicts[name][key] = value

    cpdef object get_item(self, str name, int key):
        cdef dict inner
        inner = self._dicts.get(name)
        if inner is not None:
            return inner.get(key)
        return None

    cpdef bint dict_exists(self, str name):
        return name in self._dicts

    cpdef bint key_exists(self, str name, int key):
        cdef dict inner
        inner = self._dicts.get(name)
        if inner is not None:
            return key in inner
        return False

    cpdef void remove_key(self, str name, int key):
        cdef dict inner
        inner = self._dicts.get(name)
        if inner is not None and key in inner:
            del inner[key]

    cpdef void remove_dict(self, str name):
        if name in self._dicts:
            del self._dicts[name]
