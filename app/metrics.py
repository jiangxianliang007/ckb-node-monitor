from __future__ import annotations

import logging
import time

from prometheus_client import CollectorRegistry, Gauge

from .rpc import RpcGet

logger = logging.getLogger(__name__)

BASE_LABELS = ["chain", "node_name", "node_type", "node_ip", "node_location"]


class MetricsCollector:
    def __init__(self, rpc_client: RpcGet, labels: dict[str, str]) -> None:
        self.rpc_client = rpc_client
        self.labels = labels
        self.registry = CollectorRegistry()

        self.Node_Status = Gauge("ckb_node_status", "CKB node connectivity status (local_node_info)", BASE_LABELS, registry=self.registry)
        self.Node_Get_LocalInfo = Gauge(
            "ckb_node_info",
            "CKB local node info status (local_node_info)",
            BASE_LABELS + ["node_address", "node_id", "node_version"],
            registry=self.registry,
        )
        self.Node_Get_PeerOutbound = Gauge("ckb_peers_outbound_count", "Outbound peers (get_peers)", BASE_LABELS, registry=self.registry)
        self.Node_Get_PeerInbound = Gauge("ckb_peers_inbound_count", "Inbound peers (get_peers)", BASE_LABELS, registry=self.registry)
        self.Node_Get_Light_Client_Conn = Gauge(
            "ckb_peers_light_client_count", "Connected light clients (get_peers)", BASE_LABELS, registry=self.registry
        )
        self.Node_Get_LastBlockInfo = Gauge(
            "ckb_tip_header_info",
            "Tip header info with labels from get_tip_header/get_block",
            BASE_LABELS + ["block_hash", "block_number", "block_timestamp"],
            registry=self.registry,
        )
        self.Node_Get_LastBlocknumber = Gauge(
            "ckb_tip_block_number", "Tip block number (get_tip_header)", BASE_LABELS, registry=self.registry
        )
        self.Node_Get_BlockDetail = Gauge(
            "ckb_block_commit_transactions",
            "Committed transactions in tip block (get_block)",
            BASE_LABELS,
            registry=self.registry,
        )
        self.Node_Get_BlockDetail_proposal_transactions = Gauge(
            "ckb_block_proposal_transactions",
            "Proposal transactions in tip block (get_block)",
            BASE_LABELS,
            registry=self.registry,
        )
        self.Node_Get_BlockDetail_uncles = Gauge(
            "ckb_block_uncles_count", "Uncles in tip block (get_block)", BASE_LABELS, registry=self.registry
        )
        self.Node_Get_BlockDifference = Gauge(
            "ckb_block_interval_seconds", "Tip-to-previous block interval in seconds", BASE_LABELS, registry=self.registry
        )
        self.Node_Get_BlockTimeDifference = Gauge(
            "ckb_block_time_since_last_seconds", "Current time minus tip block timestamp in seconds", BASE_LABELS, registry=self.registry
        )
        self.Node_Get_client_version = Gauge(
            "ckb_miner_client_version",
            "Miner client version marker from cellbase witness",
            BASE_LABELS + ["client_version"],
            registry=self.registry,
        )
        self.Node_Get_Pool_size = Gauge("ckb_tx_pool_total_tx_size", "Tx pool total size (tx_pool_info)", BASE_LABELS, registry=self.registry)
        self.Node_Get_Pool_cycles = Gauge("ckb_tx_pool_total_tx_cycles", "Tx pool total cycles (tx_pool_info)", BASE_LABELS, registry=self.registry)
        self.Node_Get_Pool_orphan = Gauge("ckb_tx_pool_orphan", "Tx pool orphan count (tx_pool_info)", BASE_LABELS, registry=self.registry)
        self.Node_Get_Pool_pending = Gauge("ckb_tx_pool_pending", "Tx pool pending count (tx_pool_info)", BASE_LABELS, registry=self.registry)
        self.Node_Get_Pool_proposed = Gauge("ckb_tx_pool_proposed", "Tx pool proposed count (tx_pool_info)", BASE_LABELS, registry=self.registry)
        self.Node_verify_queue_size = Gauge(
            "ckb_tx_pool_verify_queue_size", "Tx pool verify queue size (tx_pool_info)", BASE_LABELS, registry=self.registry
        )
        self.current_epoch_start_number = Gauge(
            "ckb_epoch_start_number", "Current epoch start number (get_current_epoch)", BASE_LABELS, registry=self.registry
        )
        self.current_epoch_length = Gauge("ckb_epoch_length", "Current epoch length (get_current_epoch)", BASE_LABELS, registry=self.registry)
        self.Node_ban_all = Gauge("ckb_banned_addresses_total", "Total banned addresses (get_banned_addresses)", BASE_LABELS, registry=self.registry)
        self.Node_ban_bootnode = Gauge("ckb_banned_bootnodes_count", "Banned bootnodes count (get_banned_addresses)", BASE_LABELS, registry=self.registry)
        self.Pending_Tx_Time = Gauge("ckb_tx_pool_oldest_pending_seconds", "Oldest pending tx age in seconds (get_raw_tx_pool)", BASE_LABELS, registry=self.registry)
        self.Pending_Tx_Count = Gauge("ckb_tx_pool_pending_count", "Pending tx count (get_raw_tx_pool)", BASE_LABELS, registry=self.registry)
        self.Max_ancestors_count = Gauge(
            "ckb_tx_pool_max_ancestors_count", "Max pending tx ancestors count (get_raw_tx_pool)", BASE_LABELS, registry=self.registry
        )
        self.Node_fee_rate_mean = Gauge("ckb_fee_rate_mean", "Fee rate mean (get_fee_rate_statistics)", BASE_LABELS, registry=self.registry)
        self.Node_fee_rate_median = Gauge("ckb_fee_rate_median", "Fee rate median (get_fee_rate_statistics)", BASE_LABELS, registry=self.registry)
        self.Block_Size = Gauge("ckb_block_size_bytes", "Block serialized size in bytes", BASE_LABELS, registry=self.registry)
        self.Estimate_fee_rate = Gauge("ckb_estimate_fee_rate", "Estimated fee rate (estimate_fee_rate)", BASE_LABELS, registry=self.registry)
        self.difficulty = Gauge("ckb_blockchain_difficulty", "Blockchain difficulty (get_blockchain_info)", BASE_LABELS, registry=self.registry)
        self.total_issuance = Gauge("ckb_total_issuance", "CKB total issuance in CKB", BASE_LABELS, registry=self.registry)
        self.dao_deposit = Gauge("ckb_dao_deposit", "Nervos DAO total deposit in CKB", BASE_LABELS, registry=self.registry)
        self.occupied_capacity = Gauge(
            "ckb_occupied_capacity", "On-chain occupied capacity (Knowledge Size) in CKB", BASE_LABELS, registry=self.registry
        )
        self.network_hashrate = Gauge("ckb_network_hashrate", "Estimated CKB network hashrate (H/s)", BASE_LABELS, registry=self.registry)

    def _label_values(self) -> list[str]:
        return [
            self.labels["chain"],
            self.labels["node_name"],
            self.labels["node_type"],
            self.labels["node_ip"],
            self.labels["node_location"],
        ]

    def collect(self) -> dict[str, object]:
        label_values = self._label_values()
        self.Node_Get_LastBlockInfo._metrics.clear()
        self.Node_Get_client_version._metrics.clear()
        self.Node_Get_LocalInfo._metrics.clear()

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

        if block_number >= 0:
            block_hash = self.rpc_client.get_block_hash(block_number)["blocknumber_hash"]
        else:
            block_hash = "-1"

        self.Node_Get_LastBlockInfo.labels(
            *label_values,
            str(block_hash),
            str(block_number),
            str(block_timestamp),
        ).set(float(block_timestamp))

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
            if block_timestamp >= 0:
                timestamp_diff = float((int(round(time.time() * 1000)) - block_timestamp) / 1000)
            if block_number > 0 and block_timestamp >= 0:
                previous_block_hash = self.rpc_client.get_block_hash(block_number - 1)["blocknumber_hash"]
                previous_block_detail = self.rpc_client.get_BlockDetail(str(previous_block_hash))
                previous_block_ts = int(previous_block_detail["blocknumber_timestamp"])
                if previous_block_ts >= 0:
                    block_diff = abs(float(block_timestamp - previous_block_ts)) / 1000.0
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
        difficulty_value = int(difficulty["difficulty"])
        self.difficulty.labels(*label_values).set(float(difficulty_value))

        economics = self.rpc_client.get_tip_economics()
        self.total_issuance.labels(*label_values).set(float(economics["total_issuance_ckb"]))
        self.dao_deposit.labels(*label_values).set(float(economics["dao_deposit_ckb"]))
        self.occupied_capacity.labels(*label_values).set(float(economics["occupied_capacity_ckb"]))

        consensus = self.rpc_client.get_consensus()
        epoch_duration_target = int(consensus["epoch_duration_target"])
        epoch_length = int(epoch["length"])
        hashrate = -1.0
        if difficulty_value >= 0 and epoch_duration_target > 0 and epoch_length > 0:
            avg_block_time = epoch_duration_target / epoch_length
            if avg_block_time > 0:
                hashrate = float(difficulty_value) / avg_block_time
        self.network_hashrate.labels(*label_values).set(hashrate)

        return {
            "node_status": local_info["node_status"],
            "last_blocknumber": last_block["last_blocknumber"],
            "last_block_hash": last_block["last_block_hash"],
        }
