from typing import Callable, List, Optional, Union

from typing_extensions import Literal

from pygwalker._constants import JUPYTER_BYTE_LIMIT
from pygwalker._typing import DataFrame
from pygwalker.data_parsers.base import BaseDataParser, FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker.services.cloud_service import CloudService
from pygwalker.services.data_parsers import get_parser
from pygwalker.utils.randoms import rand_str


class DataBridge:
    """Own the parser and kernel/browser data path decision for a walker."""

    def __init__(
        self,
        *,
        dataset: Union[DataFrame, Connector, str],
        field_specs: List[FieldSpec],
        cloud_computation: bool,
        kernel_computation: Optional[bool],
        kanaries_api_key: str,
        cloud_service: CloudService,
        parser_factory: Optional[Callable[..., BaseDataParser]] = None,
    ):
        create_parser = parser_factory or self.create_data_parser
        self.data_parser = create_parser(
            dataset=dataset,
            field_specs=field_specs,
            cloud_computation=cloud_computation,
            kanaries_api_key=kanaries_api_key,
            cloud_service=cloud_service,
        )
        suggest_kernel_computation = self.data_parser.data_size > JUPYTER_BYTE_LIMIT
        self.kernel_computation = suggest_kernel_computation if kernel_computation is None else kernel_computation
        self.origin_data_source = self.data_parser.to_records(500 if self.kernel_computation else None)
        self.field_specs = self.data_parser.raw_fields
        self.parse_dsl_type = self.get_parse_dsl_type(self.data_parser)
        self.dataset_type = self.data_parser.dataset_type

    @staticmethod
    def create_data_parser(
        *,
        dataset: Union[DataFrame, Connector, str],
        field_specs: List[FieldSpec],
        cloud_computation: bool,
        kanaries_api_key: str,
        cloud_service: CloudService,
    ) -> BaseDataParser:
        data_parser = get_parser(
            dataset,
            field_specs,
            other_params={"kanaries_api_key": kanaries_api_key},
        )
        if not cloud_computation:
            return data_parser

        dataset_id = cloud_service.create_cloud_dataset(
            data_parser,
            f"temp_{rand_str()}",
            False,
            True,
        )

        return get_parser(
            dataset_id,
            field_specs,
            other_params={"kanaries_api_key": kanaries_api_key},
        )

    @staticmethod
    def get_parse_dsl_type(data_parser: BaseDataParser) -> Literal["server", "client"]:
        if data_parser.dataset_type.startswith("connector"):
            return "server"
        if data_parser.dataset_type == "cloud_dataset":
            return "server"
        return "client"

    def warm_kernel_table(self) -> None:
        try:
            self.data_parser.get_datas_by_sql("SELECT 1 FROM pygwalker_mid_table LIMIT 1")
        except Exception:
            pass
