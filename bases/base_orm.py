from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, inspect, asc, desc
from typing import Optional, Type, Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.functions import count
from typing import Annotated
from fastapi.logger import logger

from bases.session_manager import get_session

SessionDep: Type[AsyncSession] = Annotated[AsyncSession, Depends(get_session)]


class BaseORM:
    """
    BaseORM class provides an abstraction layer for interacting with the database using SQLAlchemy's ORM.
    It includes methods for common CRUD operations, query execution, and validation.
    Methods:
        __init__(model: Type["DeclarativeBase"]):
            Initialize the ORM instance with a specific model.
        create(**kwargs):
            Create a new record in the database.
        get(pk: int):
            Retrieve a record by its primary key (ID).
        update(pk: int, **kwargs):
            Update a record by its primary key (ID) with the provided fields.
        delete(pk: int, model=None):
            Delete a record by its primary key (ID). Optionally, a different model can be specified.
        save(model=None):
            Save changes to the database for the given model instance. Ensures no duplicate sessions.
        all(offset: int = 0, limit: int = 100, order_by: str = None):
            Retrieve all records of the model with pagination and ordering.
        filter(offset: int = 0, limit: int = 100, order_by: str = None, **filters):
            Retrieve records that match the specified filter criteria with pagination and ordering.
        first(**filters):
            Retrieve the first record that matches the specified filter criteria.
        count():
            Count the total number of records for the model.
        exists(**filters):
            Check if any record matches the specified filter criteria.
        execute_query(query):
            Execute a custom SQLAlchemy query.
        _filter_conditions(filtered_fields: dict[str, Any] = None):
            Generate filter conditions for queries based on the provided fields.
        select_related(attrs: list[str] = None, **kwargs):
            Retrieve a record along with its related attributes.
        validate_relations(data: BaseModel):
            Validate the relationships of the model based on the provided data.
        validate_unique_fields(data: BaseModel):
            Validate that unique fields in the model do not violate constraints.
    Attributes:
        model: The SQLAlchemy model associated with this ORM instance.
    """

    model: Type["DeclarativeBase"]

    def __init__(self, session: AsyncSession, model: Type["DeclarativeBase"]):
        self.session = session
        self.model = model

    async def create(self, **kwargs):
        """
        Asynchronously creates a new instance of the model with the provided keyword arguments,
        adds it to the database session, commits the transaction, and refreshes the instance
        to reflect the latest state from the database.
        Args:
            **kwargs: Arbitrary keyword arguments representing the fields and their values
                      for the model instance to be created.
        Returns:
            instance: The newly created and persisted instance of the model.
        Raises:
            Any exceptions raised during the database session operations, such as integrity
            errors or connection issues.
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def get(self, pk: int):
        """
        Retrieve a single record from the database by its primary key.
        Args:
            pk (int): The primary key of the record to retrieve.
        Returns:
            Optional[Base]: The retrieved record as an instance of the model,
            or None if no record with the specified primary key exists.
        """
        result = await self.session.execute(
            select(self.model).filter(self.model.id == pk)
        )
        return result.scalars().first()

    async def update(self, pk, **kwargs):
        """
        Update an instance of the model with the given primary key (pk) and new values.
        Args:
            pk (Any): The primary key of the instance to update.
            **kwargs: Key-value pairs representing the fields to update and their new values.
        Returns:
            Optional[Model]: The updated instance of the model if found, otherwise None.
        Notes:
            - This method uses an asynchronous database session to fetch, update, and save the instance.
            - If the instance with the given primary key does not exist, the method returns None.
            - After updating the instance, the session is committed and the instance is refreshed.
        """
        instance = await self.session.get(self.model, pk)
        if not instance:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, pk=None, model=None):
        """
        Asynchronously deletes an instance of the specified model by primary key.
        Args:
            pk (Any): The primary key of the instance to delete.
            model (Optional[Type[Base]]): The SQLAlchemy model class. If not provided,
                the default model associated with the class will be used.
        Returns:
            bool: True if the instance was successfully deleted, False if the instance
            was not found.
        Raises:
            SQLAlchemyError: If an error occurs during the database operation.
        """
        if not model:
            if not pk:
                raise KeyError("A primary key or SQLAlchemy instance must be provided.")
            model = await self.session.get(self.model, pk)
        await self.session.delete(model)
        await self.session.commit()
        return True

    async def save(self, model=None):
        """
        Save the given model instance to the database.
        If no model is provided, the instance associated with `self.model` will be used.
        The method ensures no duplicate sessions by merging the instance into the current
        database session. After committing the changes, the instance is refreshed to reflect
        the latest state from the database.
        Args:
            model (Optional[BaseModel]): The model instance to save. Defaults to `self.model`.
        Returns:
            BaseModel: The updated and saved model instance.
        """
        model = model or self.model
        merged_instance = await self.session.merge(
            model
        )  # Ensures no duplicate sessions
        await self.session.commit()
        await self.session.refresh(merged_instance)
        return merged_instance

    async def all(
        self,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
        order_by: Optional[str] = None,
    ):
        """
        Retrieve all records of the model from the database with pagination and ordering.

        Args:
            offset (int): Number of records to skip. Defaults to 0.
            limit (int): Maximum number of records to return. Defaults to 100, max 100.
            order_by (str, optional): Column name to order by. Prefix with '-' for descending.

        Returns:
            list: A list of model instances matching the criteria.
        """
        query = select(self.model)
        query = self._apply_ordering(query, order_by)
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def filter(
        self,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
        order_by: Optional[str] = None,
        **filters,
    ):
        """
        Filters records in the database based on the provided keyword arguments with pagination and ordering.

        Args:
            offset (int): Number of records to skip. Defaults to 0.
            limit (int): Maximum number of records to return. Defaults to 100, max 100.
            order_by (str, optional): Column name to order by. Prefix with '-' for descending.
            **filters: Arbitrary keyword arguments representing the filter conditions.
                       Each key-value pair corresponds to a column and its desired value.
        Returns:
            list: A list of model instances that match the filter conditions.
        Raises:
            Exception: If there is an issue with the database session or query execution.
        Example:
            # Assuming `self.model` has a column `name`:
            results = await instance.filter(name="John Doe", offset=10, limit=20, order_by="-created_at")
        """
        query = select(self.model).where(*self._filter_conditions(filters))
        query = self._apply_ordering(query, order_by)
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def first(self, **filters):
        """
        Retrieve the first record from the database that matches the given filters.
        Args:
            **filters: Arbitrary keyword arguments representing the filter conditions
                       to apply to the query.
        Returns:
            The first matching record as an instance of the model, or None if no match is found.
        Raises:
            Any exceptions raised during the database query execution.
        """
        query = select(self.model).where(*self._filter_conditions(filters))
        result = await self.session.execute(query)
        return result.scalars().first()

    async def count(self):
        """
        Asynchronously counts the total number of records in the database table
        associated with the model.
        Returns:
            int: The total count of records in the table.
        """
        result = await self.session.execute(select(count()).select_from(self.model))
        return result.scalar()

    async def exists(self, **filters):
        """
        Asynchronously checks if a record exists in the database that matches the given filters.
        Args:
            **filters: Arbitrary keyword arguments representing the filter criteria.
        Returns:
            bool: True if a matching record exists, False otherwise.
        """
        return await self.first(**filters) is not None

    async def execute_query(self, query):
        """
        Executes a given SQL query within an asynchronous database session.
        Args:
            query: The SQL query to be executed.
        Returns:
            The result of the executed query.
        Note:
            This method uses an asynchronous session to execute the query and
            returns the result. Ensure that the query is compatible with the
            database engine being used.
        """
        result = await self.session.execute(query)
        return result

    def _filter_conditions(self, filtered_fields: dict[str, Any] = None):
        """
        Generate a list of filter conditions based on the provided dictionary of field-value pairs.
        Args:
            filtered_fields (dict[str, Any], optional): A dictionary where keys are field names
                and values are the corresponding values to filter by. Defaults to None.
        Returns:
            list: A list of filter conditions to be used in queries.
        Raises:
            AttributeError: If the specified field does not exist in the model.
        """
        filter_conditions = []
        fields = filtered_fields or {}
        for attr, value in fields.items():
            if hasattr(self.model, attr):
                filter_conditions.append(getattr(self.model, attr) == value)
            else:
                logger.warning(f"Model {self.model.__name__} does not have '{attr}' attribute")
        return filter_conditions

    def _apply_ordering(self, query, order_by: Optional[str] = None):
        """
        Apply ordering to a query based on the order_by parameter.

        Args:
            query: The SQLAlchemy query to apply ordering to
            order_by: String specifying the column to order by.
                     Prefix with '-' for descending order (e.g., '-name')

        Returns:
            The query with ordering applied
        """
        if not order_by:
            return query

        if order_by.startswith("-"):
            # Descending order
            column_name = order_by[1:]
            if hasattr(self.model, column_name):
                return query.order_by(desc(getattr(self.model, column_name)))
        else:
            # Ascending order
            if hasattr(self.model, order_by):
                return query.order_by(asc(getattr(self.model, order_by)))

        return query

    async def select_related(self, attrs: list[str] = None, **kwargs):
        """
        Asynchronously retrieves a related model instance from the database with optional
        attributes to refresh.
        Args:
            attrs (list[str], optional): A list of attribute names to refresh on the
                retrieved model instance. Defaults to an empty list.
            **kwargs: Arbitrary keyword arguments used to filter the query.
        Raises:
            AttributeError: If any attribute in `attrs` does not exist on the model.
        Returns:
            Optional[Model]: The first instance of the model that matches the filter
                conditions, with the specified attributes refreshed, or `None` if no
                matching instance is found.
        """
        attrs = attrs or []
        for attr in attrs:
            if not hasattr(self.model, attr):
                raise AttributeError(
                    f"Model {self.__name__} does not have '{attr}' attribute"
                )
        result = await self.session.execute(
            select(self.model).filter(*self._filter_conditions(kwargs))
        )
        instance = result.scalars().first()
        if not instance:
            return None
        await self.session.refresh(instance, attrs)
        return instance

    async def validate_relations(self, data: BaseModel):
        """
        Validates the relationships of a given data model instance against the database.
        This method checks if the provided data contains valid foreign key references
        for the relationships defined in the SQLAlchemy model. If a required foreign key
        value is missing or does not correspond to an existing entity in the database,
        an exception is raised.
        Args:
            data (BaseModel): The Pydantic model instance containing the data to validate.
        Raises:
            KeyError: If a required foreign key value is missing in the provided data.
            ValueError: If a foreign key value does not correspond to an existing entity
                        in the database.
        """
        data_dict = data.model_dump()
        for rel in inspect(self.model).relationships:
            for attr in dir(rel):
                if attr.startswith("_"):
                    continue
            local_col = list(rel.local_columns)[0]
            remote_side = list(rel.remote_side)[0]
            if not local_col.primary_key:
                col_val = data_dict.get(local_col.name)
                if col_val is None:
                    raise KeyError(
                        f"Key '{local_col.name}' not found in provided body."
                    )

                result = await self.session.execute(
                    select(rel.mapper.entity).filter(
                        getattr(rel.mapper.entity, remote_side.name) == col_val
                    )
                )
                if not result.first():
                    raise ValueError(
                        f"Entity({rel.mapper.entity}) with primary key: {col_val} not found."
                    )

    async def validate_unique_fields(self, data: BaseModel):
        """
        Validates that the unique fields in the provided data do not violate
        the unique constraints defined in the database model.
        Args:
            data (BaseModel): The data to validate, represented as a Pydantic model.
        Raises:
            ValueError: If the primary key is manually included in the data or if
                        a unique constraint is violated for any column.
        Notes:
            - The primary key field is excluded from validation to prevent manual
              overrides.
            - For each column marked as unique, the method checks if the provided
              value already exists in the database. If a duplicate is found, a
              `ValueError` is raised.
        """
        data_dict = data.model_dump()
        # Remove primary key from data to prevent manual override
        pk_column = inspect(self.model).primary_key[0]
        if pk_column in data_dict:
            raise ValueError(f"Cannot create or change primary key '{pk_column.name}'.")
        for column in inspect(self.model).columns:
            if column.unique:
                col_val = data_dict.get(column.name)
                if col_val is not None:
                    result = await self.session.execute(
                        select(self.model).filter(
                            getattr(self.model, column.name) == col_val
                        )
                    )
                    if result.first():
                        raise ValueError(
                            f"Unique constraint violation: '{column.name}' with value '{col_val}' already exists."
                        )

    def set_model(self, model: Type["DeclarativeBase"]):
        """Class method that returns the dependency annotation"""
        self.model = model

    @classmethod
    def instance(cls, session: SessionDep):
        """Class method that returns the dependency annotation"""
        return cls(session=session, model=cls.model)

    @classmethod
    def new_repo(cls, session: SessionDep, model):
        """Class method that returns the dependency annotation"""
        return cls(session=session, model=model)
