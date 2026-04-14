from __future__ import annotations

import logging
import time

from prometheus_client import CollectorRegistry, Gauge

from .rpc import RpcGet

logger = logging.getLogger(__name__)

BASE_LABELS = ["chain", "node_name", "node_ip", "node_location"]


class MetricsCollector:
    def __init__(self, rpc_client: RpcGet, labels: dict[str, str]) -> None:
        self.rpc_client = rpc_client
        self.labels = labels
        self.registry = CollectorRegistry()

        self.Node_Status = Gauge("node_status", "CKB node connectivity status", BASE_LABELS, registry=self.registry)
        self.Node_Get_LocalInfo = Gauge(
            "node_get_localinfo",
            "CKB local node info status",
            BASE_LABELS + ["node_address", "node_id", "node_version"],
            registry=self.registry,
        )
        self.Node_Get_PeerOutbound = Gauge("node_get_peer_outbound", "Outbound peers", BASE_LABELS, registry=self.registry)
        self.Node_Get_PeerInbound = Gauge("node_get_peer_inbound", "Inbound peers", BASE_LABELS, registry=self.registry)
        self.Node_Get_Light_Client_Conn = Gauge(
            "node_get_light_client_conn", "Connected light clients", BASE_LABELS, registry=self.registry
        )
        self.Node_Get_LastBlockInfo = Gauge(
            "node_get_last_block_info", "Last block timestamp", BASE_LABELS, registry=self.registry
        )
        self.Node_Get_LastBlocknumber = Gauge(
            "node_get_last_blocknumber", "Last block number", BASE_LABELS, registry=self.registry
        )
        self.Node_Get_BlockDetail = Gauge(
            "node_get_blockdetail_commit_transactions",
            "Committed transactions in current block",
            BASE_LABELS,
            registry=self.registry,
        )
        self.Node_Get_BlockDetail_proposal_transactions = Gauge(
            "node_get_blockdetail_proposal_transactions",
            "Proposal transactions in current block",
            BASE_LABELS,
            registry=self.registry,
        )
        self.Node_Get_BlockDetail_uncles = Gauge(
            "node_get_blockdetail_uncles", "Uncles in current block", BASE_LABELS, registry=self.registry
        )
        self.Node_Get_BlockDifference = Gauge(
            "node_get_blockdifference", "Difference between local timestamps", BASE_LABELS, registry=self.registry
        )
        self.Node_Get_BlockTimeDifference = Gauge(
            "node_get_blocktimedifference", "Current time minus tip block timestamp", BASE_LABELS, registry=self.registry
        )
        self.Node_Get_client_version = Gauge(
            "node_get_client_version",
            "Client version marker",
            BASE_LABELS + ["client_version"],
            registry=self.registry,
        )
        self.Node_Get_Pool_size = Gauge("node_get_pool_size", "Tx pool size", BASE_LABELS, registry=self.registry)
        self.Node_Get_Pool_cycles = Gauge("node_get_pool_cycles", "Tx pool cycles", BASE_LABELS, registry=self.registry)
        self.Node_Get_Pool_orphan = Gauge("node_get_pool_orphan", "Orphan tx count", BASE_LABELS, registry=self.registry)
        self.Node_Get_Pool_pending = Gauge("node_get_pool_pending", "Pending tx count", BASE_LABELS, registry=self.registry)
        self.Node_Get_Pool_proposed = Gauge("node_get_pool_proposed", "Proposed tx count", BASE_LABELS, registry=self.registry)
        self.Node_verify_queue_size = Gauge(
            "node_verify_queue_size", "Verify queue size", BASE_LABELS, registry=self.registry
        )
        self.current_epoch_start_number = Gauge(
            "current_epoch_start_number", "Current epoch start number", BASE_LABELS, registry=self.registry
        )
        self.current_epoch_length = Gauge("current_epoch_length", "Current epoch length", BASE_LABELS, registry=self.registry)
        self.Node_ban_all = Gauge("node_ban_all", "All banned addresses", BASE_LABELS, registry=self.registry)
        self.Node_ban_bootnode = Gauge("node_ban_bootnode", "Banned bootnodes", BASE_LABELS, registry=self.registry)
        self.Pending_Tx_Time = Gauge("pending_tx_time", "Oldest pending tx age in seconds", BASE_LABELS, registry=self.registry)
        self.Pending_Tx_Count = Gauge("pending_tx_count", "Pending tx count", BASE_LABELS, registry=self.registry)
        self.Max_ancestors_count = Gauge(
            "max_ancestors_count", "Max pending tx ancestors count", BASE_LABELS, registry=self.registry
        )
        self.Node_fee_rate_mean = Gauge("node_fee_rate_mean", "Fee rate mean", BASE_LABELS, registry=self.registry)
        self.Node_fee_rate_median = Gauge("node_fee_rate_median", "Fee rate median", BASE_LABELS, registry=self.registry)
        self.Block_Size = Gauge("block_size", "Block object size length", BASE_LABELS, registry=self.registry)
        self.Estimate_fee_rate = Gauge("estimate_fee_rate", "Estimated fee rate", BASE_LABELS, registry=self.registry)
        self.difficulty = Gauge("difficulty", "Chain difficulty", BASE_LABELS, registry=self.registry)

    def _label_values(self) -> list[str]:
        return [
            self.labels["chain"],
            self.labels["node_name"],
            self.labels["node_ip"],
            self.labels["node_location"],
        ]

    def collect(self) -> dict[str, object]:
        label_values = self._label_values()

        local_info = self.rpc_client.get_node_info()
        self.Node_Status.labels(*label_values).set(float(local_info["node_status"]))
        self.Node_Get_LocalInfo.labels(
            *label_values,
            str(local_info["node_address"]),
            str(local_info["node_id"]),
            str(local_info["node_version"]),
        ).set(float(local_info["node_status"]))

        peers = self.rpc_client.get_peer_count()
        self.Node_Get_PeerOutbound.labels(*label_values).set(float(peers["peer_outbound"]))
        self.Node_Get_PeerInbound.labels(*label_values).set(float(peers["peer_inbound"]))
        self.Node_Get_Light_Client_Conn.labels(*label_values).set(float(peers["light_clients"]))

        last_block = self.rpc_client.get_LastBlockInfo()
        block_number = int(last_block["last_blocknumber"])
        block_timestamp = int(last_block["last_block_timestamp"])
        self.Node_Get_LastBlocknumber.labels(*label_values).set(float(block_number))
        self.Node_Get_LastBlockInfo.labels(*label_values).set(float(block_timestamp))

        if block_number >= 0:
            block_hash = self.rpc_client.get_block_hash(block_number)["blocknumber_hash"]
        else:
            block_hash = "-1"

        block_detail = self.rpc_client.get_BlockDetail(str(block_hash))
        self.Node_Get_BlockDetail.labels(*label_values).set(float(block_detail["commit_transactions"]))
        self.Node_Get_BlockDetail_proposal_transactions.labels(*label_values).set(
            float(block_detail["proposal_transactions"])
        )
        self.Node_Get_BlockDetail_uncles.labels(*label_values).set(float(block_detail["uncles"]))
        self.Node_Get_client_version.labels(*label_values, str(block_detail["client_version"])).set(1.0)

        timestamp_diff = -1.0
        block_diff = -1.0
        try:
            block_detail_ts = int(block_detail["blocknumber_timestamp"])
            if block_detail_ts >= 0 and block_timestamp >= 0:
                block_diff = float(block_timestamp - block_detail_ts)
                timestamp_diff = float((int(round(time.time() * 1000)) - block_timestamp) / 1000)
        except (TypeError, ValueError):
            logger.debug("Failed to compute block timing differences")

        self.Node_Get_BlockDifference.labels(*label_values).set(block_diff)
        self.Node_Get_BlockTimeDifference.labels(*label_values).set(timestamp_diff)

        pool = self.rpc_client.get_LastPoolInfo()
        self.Node_Get_Pool_size.labels(*label_values).set(float(pool["total_tx_size"]))
        self.Node_Get_Pool_cycles.labels(*label_values).set(float(pool["total_tx_cycles"]))
        self.Node_Get_Pool_orphan.labels(*label_values).set(float(pool["orphan"]))
        self.Node_Get_Pool_pending.labels(*label_values).set(float(pool["pending"]))
        self.Node_Get_Pool_proposed.labels(*label_values).set(float(pool["proposed"]))
        self.Node_verify_queue_size.labels(*label_values).set(float(pool["verify_queue_size"]))

        epoch = self.rpc_client.get_current_epoch()
        self.current_epoch_start_number.labels(*label_values).set(float(epoch["start_number"]))
        self.current_epoch_length.labels(*label_values).set(float(epoch["length"]))

        ban = self.rpc_client.get_banned_addresses()
        self.Node_ban_all.labels(*label_values).set(float(ban["ban_all"]))
        self.Node_ban_bootnode.labels(*label_values).set(float(ban["ban_bootnode"]))

        pending_tx = self.rpc_client.get_pending_tx()
        self.Pending_Tx_Time.labels(*label_values).set(float(pending_tx["first_pending_tx_time"]))
        self.Pending_Tx_Count.labels(*label_values).set(float(pending_tx["pending_tx_count"]))
        self.Max_ancestors_count.labels(*label_values).set(float(pending_tx["max_ancestors_count"]))

        fee_stats = self.rpc_client.get_fee_rate_statistics()
        self.Node_fee_rate_mean.labels(*label_values).set(float(fee_stats["mean"]))
        self.Node_fee_rate_median.labels(*label_values).set(float(fee_stats["median"]))

        block_size = self.rpc_client.get_BlockSize(str(block_hash))
        self.Block_Size.labels(*label_values).set(float(block_size["block_size"]))

        estimate_fee = self.rpc_client.estimate_fee_rate()
        self.Estimate_fee_rate.labels(*label_values).set(float(estimate_fee["estimate_fee_rate"]))

        difficulty = self.rpc_client.get_difficulty()
        self.difficulty.labels(*label_values).set(float(difficulty["difficulty"]))

        return {
            "node_status": local_info["node_status"],
            "last_blocknumber": last_block["last_blocknumber"],
            "last_block_hash": last_block["last_block_hash"],
        }
