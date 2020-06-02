import uuid
from typing import List, Sequence, Collection, Container, Union


class WithRegistryMeta(type):
    def __new__(mcs, name, bases, attrs):
        if not any(hasattr(base, 'registry') for base in bases) and 'from_yaml' not in attrs:
            attrs['registry'] = {}
        cls = type.__new__(mcs, name, bases, attrs)
        if 'from_yaml' not in attrs:
            cls.registry[cls.registry_type] = cls
        return cls

def cast_object_per_annotation(annotation, data, layout):
    pass

def cast_per_annotation(annotations, data, layout):
    for key in data:
        if key.endswith('_id'):
            key, data[key[:-3]] = key[:-3], layout.by_id[data.pop(key)]
            if key in annotations and not isinstance(data[key], annotations[key]):
                raise ValueError("Referenced object not of right type")
            continue
        annotation = annotations.get(key)
        if annotation:
            data[key] = cast_object_per_annotation(data[key])



class WithRegistry(metaclass=WithRegistryMeta):
    registry_type = None

    def __init__(self, *, id=None, layout):
        self.id = id or str(uuid.uuid4())
        self.layout = layout
        if self.layout:
            if self.layout.by_id.get(self.id) not in (None, self):
                raise AssertionError("Can't reuse an ID for a new object")
            self.layout.by_id[self.id] = self

    def serialize(self):
        data = {
            'id': self.id,
        }
        if self.registry_type:
            data['type'] = self.registry_type
        return data

    @classmethod
    def from_yaml(cls, *, layout, type=None, **data):
        actual_cls = cls.registry[type]
        actual_cls.__mro__
        init_annotations = {}
        for super_cls in reversed(actual_cls.__mro__):
            if hasattr(super_cls.__init__, '__annotations__'):
                init_annotations.update(super_cls.__init__.__annotations__)
        for key in list(data):
            annotation = init_annotations.get(key)
            if key.endswith('_id'):
                new_key = key[:-3]
                data[new_key] = layout.by_id[data.pop(key)]
                if new_key in init_annotations and not isinstance(data[new_key], init_annotations[new_key]):
                    raise ValueError("Referenced object not of right type")
            if isinstance(annotation, WithRegistryMeta) and not isinstance(data[new_key], init_annotations[new_key]):
                data[key] = init_annotations[key].from_yaml(layout, **data[key])
            elif annotation and isinstance(annotation, List):
                pass
            elif key in init_annotations and isinstance(data[key], dict):
                data[key] = init_annotations[key](**data[key])
        return cls.registry[type](layout=layout, **data)
