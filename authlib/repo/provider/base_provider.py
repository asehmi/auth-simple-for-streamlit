from abc import ABC, abstractmethod
from typing import List, Literal

class StorageProvider(ABC):
    @abstractmethod
    def __init__(self, allow_db_create=False, if_table_exists: Literal['ignore', 'recreate'] = 'ignore'):
        pass

    ### MAIN INTERFACE ###
    # Function args are the split parts of a typical db (sql) query.
    # I've done this so it's easier to implement different concrete providers.
    # 
    # fields  ==> cols | aggregations
    # conds   ==> where clause
    # modifer ==> projection | sort | group

    @abstractmethod
    def close_database(self) -> None:
        """Shuts down the database."""
        pass

    # UPDATE/CREATE
    @abstractmethod
    def upsert(self, context: dict=None) -> None:
        """Updates or inserts a new user record with supplied data (cols + value dict)."""
        pass

    # READ
    @abstractmethod
    def query(self, context: dict=None) -> List[dict]:
        """Executes a query on users table and returns rows as list of dicts."""
        pass

    # DELETE
    @abstractmethod
    def delete(self, context: dict=None) -> None:
        """Deletes record from users table."""
        pass

