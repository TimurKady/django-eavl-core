# -*- coding: utf-8 -*-
"""
WrapObject — dynamic wrap adapter over EAVL-based EntityModel

This class wraps an entity instance and allows working with it as an object
with dynamically bound attributes.

Used for cases where nested structures are needed, simulating access like:
    obj.property.value
    obj.relationships[0].title

It provides utilities to:
- populate itself from a dictionary (recursively);
- reflect current state of the entity via `get_data()`;
- apply changes via `save()`;
- reload from DB via `refresh_from_db()`;
- convert back to dict for API or further processing.

Version: 0.0.1
Author: Timur Kady
Email: timurkady@yandex.com
"""


class WrapObject:
    """Phantom object class to wrap EntityModel with nested attributes."""

    def __init__(self, entity: object = None, entity_class: int = None,
                 parent: object = None, title: str = None):
        """
        Initialize a phantom object.

        - from an existing entity (if `entity` is provided), or
        - create a new one using `entity_class` and `parent`.

        :param entity: Existing entity instance to wrap
        :param entity_class: ID of the entity class to create
        :param parent: Parent node for tree structure (required for new entity)
        :param title: Title for the entity
        """
        if entity is None:
            if not entity_class:
                raise ValueError("Cannot determine model: entity_class is not provided.")  # noqa: D501
            try:
                model = entity_class.entities.model
            except AttributeError:
                raise ValueError("Cannot determine model: entity_class must have reverse relation to entities.")  # noqa: D501

            kwards = {
                "entity_class": entity_class,
                "parent": parent,
                "title": title,
            }
            entity = model.create_entity(**kwards)
        self.entity = entity
        loaded = self.entity.get_data()
        self.dict_to_attributes(loaded)

    def dict_to_attributes(self, dictionary):
        """
        Convert python dict to attributes.

        Recursively transforms dict/list structure into attribute-accessible
        nested objects.
        """
        for key in dictionary:
            value = dictionary[key]
            if isinstance(value, dict):
                setattr(self, key, SubObject(value, self.entity))
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, dict):
                        new_list.append(SubObject(item, self.entity))
                    else:
                        new_list.append(item)
                setattr(self, key, new_list)
            else:
                setattr(self, key, value)

    def __contains__(self, key):
        """Return True if the object contains the specified string object."""
        return hasattr(self, key)

    def refresh_from_db(self):
        """
        Reload entity from DB and rebind all attributes.

        Ensures self reflects current DB state via `get_data()`.
        Removes old attributes before applying new.
        """
        self.entity.refresh_from_db()
        for key in list(vars(self).keys()):
            if key != "entity":
                delattr(self, key)
        updated_data = self.entity.get_data()
        self.dict_to_attributes(updated_data)

    def to_dict(self):
        """
        Convert ModelObject back to dictionary.

        Recursively unpacks ModelObject into dict form.
        Useful for API, export, or `.save()`.
        """
        result = {}
        for key, value in vars(self).items():
            if isinstance(value, SubObject):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, SubObject):
                        new_list.append(item.to_dict())
                    else:
                        new_list.append(item)
                result[key] = new_list
            else:
                result[key] = value
        return result

    def validate(self):
        """Validate object without save."""
        data = self.to_dict()
        self.entity.validate(data)

    def save(self, *args, **kwargs):
        """
        Persist object changes to underlying entity.

        Uses `to_dict()` and pushes data to `entity.set_data(...)`
        """
        data = self.to_dict()
        self.entity.set_data(data, validate=True)

    def delete(self):
        """Delete the underlying entity and drop this phantom object."""
        self.entity.delete()
        super().__del__()

    def __repr__(self):
        """Return string representation of the object."""
        attrs = vars(self)
        return f"{self.__class__.__name__}({attrs})"


class SubObject(WrapObject):
    """
    Lightweight subobject used for nested dictionary deserialization.

    Does not call entity.get_data() again.
    """

    def __init__(self, data: dict, entity: object):
        """Init object."""
        self.entity = entity
        self.dict_to_attributes(data)
