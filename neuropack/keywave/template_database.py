from json import dump, dumps, loads
from typing import List, Tuple, Union

import numpy as np
from numpy.typing import NDArray


class TemplateDatabase():
    @classmethod
    def construct_from_dict(cls, data: dict[str, List[NDArray]]):
        """Construct a TemplateDatabase instance from a dictionary of templates.

        :param data: A dictionary of templates, with the keys representing the names of the templates and the values being lists of NDArrays representing the templates themselves.
        :type data: dict[str, List[NDArray]]
        :return: A new TemplateDatabase instance containing all of the templates in the provided dictionary.
        :rtype: TemplateDatabase
        """
        assert isinstance(data, dict)

        instance = cls()
        for k, v in data.items():
            assert isinstance(k, str)
            assert isinstance(v, List)
            for t in v:
                instance.add_template(k, t)

        return instance

    @classmethod
    def construct_from_json(cls, data: str):
        """Construct TemplateDatabase from json string representation.

        :param data: JSON data as string
        :type data: str
        :return: TemplateDatabase object
        :rtype: TemplateDatabase
        """
        d = loads(data)
        instance = cls()
        for k, v in d.items():
            assert isinstance(k, str)
            assert isinstance(v, List)
            for t in v:
                instance.add_template(k, np.array(t))
        return instance

    def __init__(self) -> None:
        """Constructor.
        """
        self.internal_data = dict()

    def get_templates(
            self, id: str) -> Tuple[bool, Union[List[NDArray], None]]:
        """Get templates for given id. Returns a tuple with a bool indicating whether the id was found and, if it was, a list of templates. If the id was not found, the second element of the tuple will be None.

        :param id: Id to search for in the database.
        :type id: str
        :return: Tuple with a bool indicating whether the id was found and, if it was, a list of templates.
        :rtype: Tuple[bool, Union[List[NDArray], None]]
        """
        if id not in self.internal_data:
            return (False, None)

        return (True, self.internal_data[id])

    def add_template(self, id: str, template: NDArray) -> None:
        """Add a single template for given id. If the id is not in the database, it will be added. If the id is already in the database, the template will be appended to the list of templates for that id.

        :param id: Id to add template for.
        :type id: str
        :param template: Template to add.
        :type template: NDArray
        """
        if id not in self.internal_data:
            self.internal_data[id] = []

        self.internal_data[id].append(template)

    def get_all_idents(self) -> List[str]:
        """Get a list of all identities in the database."""
        return list(self.internal_data.keys())

    def remove_identity(self, id: str) -> None:
        """Remove identity from database. If the identity is not in the database, nothing will happen.

        :param id: Id to remove.
        :type id: str
        """
        if id in self.internal_data:
            del self.internal_data[id]

    def save(self, path: str):
        """Save database as json file.

        :param path: Path to file.
        :type path: str
        """
        if not path.endswith("json"):
            path += ".json"

        # Make database serializable
        s_data = {k: [a.tolist() for a in v]
                  for (k, v) in self.internal_data.items()}

        out_file = open(path, "w")
        dump(s_data, out_file)

    def to_json(self):
        """Get json representation of database."""
        s_data = {k: [a.tolist() for a in v]
                  for (k, v) in self.internal_data.items()}
        return dumps(s_data)

    def __eq__(self, other: object) -> bool:
        if len(self.internal_data) != len(other.internal_data):
            return False

        for k, v in self.internal_data.items():
            if k not in other.internal_data:
                return False

            v_other = other.internal_data[k]

            if len(v) != len(v_other):
                return False

            for i in range(len(v)):
                if not np.array_equal(v[i], v_other[i]):
                    return False

        return True