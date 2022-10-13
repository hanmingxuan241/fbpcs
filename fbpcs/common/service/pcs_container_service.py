#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# pyre-strict

from typing import Dict, List, Optional

from fbpcp.entity.cluster_instance import Cluster
from fbpcp.entity.container_instance import ContainerInstance
from fbpcp.entity.container_type import ContainerType
from fbpcp.error.pcp import PcpError
from fbpcp.service.container import ContainerService
from fbpcp.service.container_aws import AWSContainerService
from fbpcs.common.entity.pcs_container_instance import PCSContainerInstance
from fbpcs.experimental.cloud_logs.aws_log_retriever import AWSLogRetriever
from fbpcs.experimental.cloud_logs.log_retriever import LogRetriever
from fbpcs.private_computation.service.utils import deprecated
from fbpcp.service.log_cloudwatch import CloudWatchLogService


class PCSContainerService(ContainerService):
    def __init__(
        self,
        inner_container_service: ContainerService,
        log_retriever: Optional[LogRetriever] = None,
    ) -> None:
        self.inner_container_service: ContainerService = inner_container_service
        self.log_retriever: Optional[LogRetriever] = log_retriever
        if not self.log_retriever:
            if isinstance(self.inner_container_service, AWSContainerService):
                self.log_retriever = AWSLogRetriever()
                self.log_retriever.cloudwatch_log_service_args = {"kls": CloudWatchLogService, "args": {}}

    def get_region(
        self,
    ) -> str:
        return self.inner_container_service.get_region()

    def get_cluster(
        self,
    ) -> str:
        return self.inner_container_service.get_cluster()

    def create_instance(
        self,
        container_definition: str,
        cmd: str,
        env_vars: Optional[Dict[str, str]] = None,
        container_type: Optional[ContainerType] = None,
    ) -> ContainerInstance:
        instance = self.inner_container_service.create_instance(
            container_definition=container_definition,
            cmd=cmd,
            env_vars=env_vars,
            container_type=container_type,
        )
        log_url = None
        if self.log_retriever:
            log_url = self.log_retriever.get_log_url(instance.instance_id)

        return PCSContainerInstance.from_container_instance(instance, log_url)

    def create_instances(
        self,
        container_definition: str,
        cmds: List[str],
        env_vars: Optional[Dict[str, str]] = None,
        container_type: Optional[ContainerType] = None,
    ) -> List[ContainerInstance]:
        return [
            self.create_instance(
                container_definition=container_definition,
                cmd=cmd,
                env_vars=env_vars,
                container_type=container_type,
            )
            for cmd in cmds
        ]

    def get_instance(self, instance_id: str) -> Optional[ContainerInstance]:
        instance = self.inner_container_service.get_instance(instance_id)
        if instance is not None:
            log_url = None
            if self.log_retriever:
                log_url = self.log_retriever.get_log_url(instance_id)
            return PCSContainerInstance.from_container_instance(instance, log_url)

    def get_instances(
        self, instance_ids: List[str]
    ) -> List[Optional[ContainerInstance]]:
        return [self.get_instance(instance_id) for instance_id in instance_ids]

    def cancel_instance(self, instance_id: str) -> None:
        return self.inner_container_service.cancel_instance(instance_id)

    def cancel_instances(self, instance_ids: List[str]) -> List[Optional[PcpError]]:
        return self.inner_container_service.cancel_instances(instance_ids)

    def get_current_instances_count(self) -> int:
        return self.inner_container_service.get_current_instances_count()

    @deprecated(
        "validate_container_definition is no longer a public method in container service"
    )
    def validate_container_definition(self, container_definition: str) -> None:
        pass

    def get_cluster_instance(self) -> Cluster:
        raise NotImplementedError
