"""
Base business logic and operation classes for handling generic CRUD operations
with validation, pre-processing, and post-processing hooks.
"""
from typing import Optional, Dict, Any, Annotated
from fastapi import Query, Request
from typing import Type
from pydantic import BaseModel
from bases.base_orm import BaseORM, SessionDep


class BaseBusinessLogic:
    """
    Base class for business logic operations.
    """

    repo: BaseORM
    schema_out: Type["BaseModel"]

    def __init__(
            self,
            request: Request,
            session: SessionDep,
    ):
        """
        Initialize with a database session.
        """
        self.session = session
        self.repo = self.repo.instance(session)


class Operation(BaseBusinessLogic):
    """
    Generic operation with validation, pre, main, and post steps.
    """

    async def operation(self, *args, **kwargs):
        """
        Execute the operation lifecycle.
        """
        await self.operation_validation(*args, **kwargs)
        await self.pre_operation(*args, **kwargs)
        instance = await self._operation(*args, **kwargs)
        await self.on_operation(*args, **kwargs)
        return self.schema_out.model_validate(instance, from_attributes=True)

    async def operation_validation(self, *args, **kwargs):
        """
        Validate before the operation.
        """
        pass

    async def pre_operation(self, *args, **kwargs):
        """
        Run before the operation.
        """
        pass

    async def _operation(self, *args, **kwargs):
        """
        Perform the main operation.
        """
        pass

    async def on_operation(self, *args, **kwargs):
        """
        Run after the operation.
        """
        pass


class CreateOperation(BaseBusinessLogic):
    """
    A class that handles the creation of an operation with validation, pre-processing,
    and post-processing steps.
    """

    async def create(self, data: BaseModel):
        """
        Handles the creation of a new instance.
        """
        await self.create_validation(data)
        data = await self.pre_create(data)
        instance = await self._create(data)
        await self.on_create(instance)
        return self.schema_out.model_validate(instance, from_attributes=True)

    async def create_validation(self, data: BaseModel):
        """
        Validates the provided data by performing relation and uniqueness checks.
        """
        await self.repo.validate_relations(data)
        await self.repo.validate_unique_fields(data)

    async def pre_create(self, data: BaseModel):
        """
        Pre-processing hook that is executed before creating a resource.
        """
        data = data.model_dump(exclude_none=True)
        return data

    async def _create(self, data: dict):
        """
        Creates a new record in the database using the provided data.
        """
        return await self.repo.create(**data)

    async def on_create(self, instance):
        """
        Handle the creation event for a given instance.
        """
        pass


class RetrieveOperation(BaseBusinessLogic):
    """
    A class that handles the retrieval of an operation with validation, pre-processing,
    and post-processing steps.
    """

    async def get(self, pk: int):
        """
        Handles the retrieval of an instance by its primary key.
        """
        await self.pre_get(pk)
        instance = await self._get(pk)
        await self.get_validation(pk, instance)
        await self.on_get(instance)
        return self.schema_out.model_validate(instance, from_attributes=True)

    async def pre_get(self, pk: int):
        """Pre-processing hook that is executed before retrieving a resource."""
        pass

    async def _get(self, pk: int):
        """Retrieves an instance from the database using the provided primary key."""
        return await self.repo.get(pk=pk)

    async def get_validation(self, pk: int, instance):
        """Validates the retrieved instance, ensuring it exists."""
        if not instance:
            raise KeyError(f"Object({self.repo.model}) with given id: {pk} not found. ")

    async def on_get(self, instance):
        """Handles the post-retrieval event for a given instance."""
        pass


class ListOperation(BaseBusinessLogic):
    """
    A class that handles listing operations with validation, pre-processing,
    and post-processing steps. Now supports pagination and ordering.
    """

    async def list(
        self,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
        order_by: Optional[str] = None,
    ):
        """
        Handles the retrieval of multiple instances with pagination and ordering.

        """
        # Create a params object to pass pagination info through the pipeline
        list_params = {"offset": offset, "limit": limit, "order_by": order_by}

        await self.list_validation(list_params)
        await self.pre_list(list_params)
        instances = await self._list(list_params)
        await self.on_list(list_params)

        return [
            self.schema_out.model_validate(instance, from_attributes=True) for instance in instances
        ]

    async def list_validation(self, params: Dict[str, Any]):
        """
        Validates before listing instances.
        """
        pass

    async def pre_list(self, params: Dict[str, Any]):
        """
        Pre-processing hook that is executed before retrieving the list of resources.

        """
        pass

    async def _list(self, params: Dict[str, Any]):
        """
        Retrieves instances from the database with pagination and ordering.
        """
        return await self.repo.filter(
            offset=params["offset"], limit=params["limit"], order_by=params["order_by"], deleted_at=None
        )

    async def on_list(self, params: Dict[str, Any]):
        """
        Handles the post-listing event after instances are retrieved.
        """
        pass


class FilterOperation(BaseBusinessLogic):
    """
    A class that handles filtering operations with validation, pre-processing,
    and post-processing steps. Supports complex filtering, pagination, and ordering.
    """

    async def filter(
        self,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
        order_by: Optional[str] = None,
    ):
        """
        Handles the retrieval of filtered instances with pagination and ordering.
        """

        if hasattr(self.repo.model, "deleted_at"):
            filters["deleted_at"] = None
        filter_params = {
            "filters": filters,
            "offset": offset,
            "limit": limit,
            "order_by": order_by,
        }

        await self.filter_validation(filter_params)
        await self.pre_filter(filter_params)
        instances = await self._filter(filter_params)
        await self.on_filter(filter_params)

        return [
            self.schema_out.model_validate(instance, from_attributes=True) for instance in instances
        ]

    async def filter_from_query_params(
        self,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
        order_by: Optional[str] = None,
        **query_filters,
    ):
        """
        Handles filtering using query parameters directly.
        """
        # Remove None values from query_filters
        clean_filters = {k: v for k, v in query_filters.items() if v is not None}

        return await self.filter(
            filters=clean_filters, offset=offset, limit=limit, order_by=order_by
        )

    async def filter_validation(self, params: Dict[str, Any]):
        """
        Validates before filtering instances.
        """
        # Validate that filter keys are valid model attributes
        filters = params.get("filters", {})
        if hasattr(self, "repo") and hasattr(self.repo, "model"):
            for filter_key in filters.keys():
                if not hasattr(self.repo.model, filter_key):
                    raise ValueError(f"Invalid filter field: {filter_key}")

    async def pre_filter(self, params: Dict[str, Any]):
        """
        Pre-processing hook that is executed before filtering resources.
        """
        pass

    async def _filter(self, params: Dict[str, Any]):
        """
        Retrieves filtered instances from the database.
        """
        filters = params["filters"]
        return await self.repo.filter(
            offset=params["offset"],
            limit=params["limit"],
            order_by=params["order_by"],
            **filters,
        )

    async def on_filter(self, params: Dict[str, Any]):
        """
        Handles the post-filtering event after instances are retrieved.
        """
        pass


class UpdateOperation(BaseBusinessLogic):

    async def update(self, pk: int, data: BaseModel):
        await self.update_validation(pk, data)
        data = await self.pre_update(pk, data)
        instance = await self._update(pk, data)
        await self.on_update(instance)
        return self.schema_out.model_validate(instance, from_attributes=True)

    async def update_validation(self, pk: int, data: BaseModel):
        await self.repo.validate_relations(data)
        await self.repo.validate_unique_fields(data)

    async def pre_update(self, pk: int, data: BaseModel):
        data = data.model_dump(exclude_none=True)
        return data

    async def _update(self, pk: int, data: dict):
        instance = await self.repo.get(pk=pk)
        for key, value in data.items():
            setattr(instance, key, value)
        await self.repo.save(instance)
        return instance

    async def on_update(self, instance):
        pass


class DeleteOperation(BaseBusinessLogic):
    """
    A class that handles deleting an operation with validation, pre-processing,
    and post-processing steps.
    """

    async def delete(self, pk: int):
        """
        Handles the deletion of an instance by its primary key.
        """
        await self.delete_validation(pk)
        await self.pre_delete(pk)
        deleted = await self._delete(pk)
        await self.on_delete(pk, deleted)
        return {"deleted": deleted}

    async def delete_validation(self, pk: int):
        """Validates before deleting an instance."""
        pass

    async def pre_delete(self, pk: int):
        """Pre-processing hook that is executed before deleting a resource."""
        pass

    async def _delete(self, pk: int):
        """Deletes an instance from the database using the provided primary key."""
        instance = await self.repo.get(pk=pk)
        if not instance:
            return False

        await self.repo.delete(instance)
        return True

    async def on_delete(self, pk: int, deleted: bool):
        """Handles the post-deletion event after an instance is deleted."""
        pass


class GenericBusinessLogic(
    Operation,
    CreateOperation,
    RetrieveOperation,
    ListOperation,
    FilterOperation,
    UpdateOperation,
    DeleteOperation,
):
    pass

    async def update_validation(self, pk: int, data: BaseModel):
        pass

    async def create_validation(self, data: BaseModel):
        pass