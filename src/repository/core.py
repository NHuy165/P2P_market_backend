from enum import Enum
from typing import Any, Generic, TypeVar, get_type_hints

from pydantic import BaseModel, TypeAdapter, ValidationError
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import SQLModel, col
from sqlmodel.sql.expression import SelectOfScalar

from ..exceptions.core import (
    ExceptionInvalidField_400,
    ExceptionRequest_400,
    ExceptionSortContradiction_400,
    ExceptionType_400,
)

# ----- Criterion classes ----- #


class CompareOperator(str, Enum):
    EQ = "eq"
    NE = "ne"

    GT = "gt"
    GE = "ge"

    LT = "lt"
    LE = "le"


class ObjectType(str, Enum):
    ITEM = "Item"
    ORDER = "Order"
    USER = "User"
    TRANSACTION = "Transaction"


class Criterion:
    """
    Criteria are used for dynamic sorting and searching.
    """

    def __init__(self, field: str):
        self.field = field


class CriterionGet(Criterion):
    def __init__(
        self, field: str, value: Any, op: CompareOperator = CompareOperator.EQ
    ):
        super().__init__(field)

        self.value = value
        self.op = op


class CriterionSort(Criterion):
    def __init__(self, field: str, ascending: bool = True):
        super().__init__(field)

        self.ascending = ascending


# ----- Criterion input ----- #


class CriterionInput(BaseModel):
    field: str


class CriterionGetInput(CriterionInput):
    value: Any
    op: CompareOperator = CompareOperator.EQ


class CriterionSortInput(CriterionInput):
    ascending: bool = True


# ----- Base Get class ----- #

ModelType = TypeVar("ModelType", bound=SQLModel)


class GetObject(Generic[ModelType]):
    """
    Used together with the Criterion classes for dynamic searching, sorting and filtering.
    'base' system allows automatic enforcement of a few common rules.
    """

    def __init__(self):
        self.model_type: ObjectType
        self.model: type[ModelType]
        self.query: SelectOfScalar[ModelType]
        self.sort_criteria = dict()
        self.base = False

        mapper = inspect(self.model)
        self.model_column_names = list(mapper.columns.keys())
        self.model_relationship_names = list(mapper.relationships.keys())

    def eager_load(self, attrs_str: list[str]):
        for attr_str in attrs_str:
            if attr_str not in self.model_relationship_names:
                raise ExceptionInvalidField_400(self.model_type, attr_str)

            attr = getattr(self.model, attr_str)
            self.query = self.query.options(selectinload(attr))

    def eager_load_to_output_model(self, output_model: type[SQLModel]):
        col_names = inspect(output_model).columns.keys()
        attrs_str = []

        for key in col_names:
            if key in self.model_relationship_names:
                attrs_str.append(key)

        self.eager_load(attrs_str)

    def eager_load_all(self):
        mapper = inspect(self.model)

        attrs_str = [rel.key for rel in mapper.relationships]

        self.eager_load(attrs_str)

    def convert_pydantic(self, criterion: CriterionInput) -> Criterion:
        """
        Converts from pydantic BaseModel to the normal Criterion.
        """
        if isinstance(criterion, CriterionGetInput):
            return CriterionGet(**criterion.model_dump())
        else:
            return CriterionSort(**criterion.model_dump())

    # Function for applying criteria
    def apply_criterion(self, criterion: Criterion | CriterionInput):
        """
        Automatically validate attribute name and type before applying.
        """
        if isinstance(criterion, CriterionInput):
            criterion = self.convert_pydantic(criterion)

        if criterion.field not in self.model_column_names:
            raise ExceptionInvalidField_400(self.model_type, criterion.field)

        attr = getattr(self.model, criterion.field)

        # Get
        if isinstance(criterion, CriterionGet):
            try:
                attr_type = get_type_hints(self.model)[criterion.field]
                adapter = TypeAdapter(attr_type)
                criterion.value = adapter.validate_python(criterion.value)

            except ValidationError:
                raise ExceptionType_400(str(attr_type))

            if criterion.op == CompareOperator.EQ:
                self.query = self.query.where(attr == criterion.value)
            if criterion.op == CompareOperator.NE:
                self.query = self.query.where(attr != criterion.value)

            if criterion.op == CompareOperator.LE:
                self.query = self.query.where(attr <= criterion.value)
            if criterion.op == CompareOperator.LT:
                self.query = self.query.where(attr < criterion.value)

            if criterion.op == CompareOperator.GE:
                self.query = self.query.where(attr >= criterion.value)
            if criterion.op == CompareOperator.GT:
                self.query = self.query.where(attr > criterion.value)

        # Sort
        elif isinstance(criterion, CriterionSort):
            # Sorted by both ascending and descending.
            if (
                self.sort_criteria.get(criterion.field, criterion.ascending)
                != criterion.ascending
            ):
                raise ExceptionSortContradiction_400(
                    criterion.field, self.model.__name__
                )
            else:
                self.sort_criteria[criterion.field] = criterion.ascending

            if criterion.ascending:
                self.query = self.query.order_by(col(attr).asc())
            else:
                self.query = self.query.order_by(col(attr).desc())

    # Utility functions
    def get_by(self, field: str, value: Any):
        """
        Utility function for applying a get criterion with the equals operator.
        """
        crit = CriterionGet(field, value)

        self.apply_criterion(crit)

    def sort_by(self, field: str, ascending: bool):
        """
        Utility function for applying a sort criterion.
        """
        crit = CriterionSort(field, ascending=ascending)

        self.apply_criterion(crit)

    # Base get function, enforce necessary stuff and provide default sort order.
    def get(
        self,
        criteria: list[Criterion] | list[CriterionInput] = [],
        with_for_update: bool = False,
    ):
        if not self.base:
            raise ExceptionRequest_400(
                f"{self.model.__name__} getter didn't receive base type (public, private or admin)."
            )
        if criteria is not None:
            for crit in criteria:
                self.apply_criterion(crit)

        # Default sort order
        if len(self.sort_criteria) == 0:
            crit = CriterionSort("id")
            self.apply_criterion(crit)

        if with_for_update:
            self.query = self.query.with_for_update()

    # Get one
    async def get_one(
        self,
        session: AsyncSession,
        criteria: list[Criterion] | list[CriterionInput] = [],
        with_for_update: bool = False,
    ) -> ModelType | None:
        self.get(criteria, with_for_update=with_for_update)

        result = await session.execute(self.query)

        return result.scalars().first()

    # Get many
    async def get_many(
        self,
        session: AsyncSession,
        criteria: list[Criterion] | list[CriterionInput] = [],
        with_for_update: bool = False,
    ) -> list[ModelType]:
        self.get(criteria, with_for_update=with_for_update)

        result = await session.execute(self.query)

        return list(result.scalars().all())
